from flask import Flask, request, jsonify, send_from_directory, send_file
from pathlib import Path
import os

# -------------------------------------
# IMPORT SERVICES
# -------------------------------------
from services.generator import gpt_generate_html
from services.validator import validate as validate_html
from services.sanitize import sanitize_ticker, clamp_years
from services.storage import save_report
from services.obs import log_event
from services.ratelimit import allow
from rules_engine import build_prompt


TITLE_REQUIRED = "DLENS Disruptor Spotlight"

API_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = API_DIR / "resources"
REPORTS_ROOT = API_DIR.parent / "reports"

app = Flask(__name__)


# -------------------------------------
# FIX HTML <title>
# -------------------------------------
def _enforce_required_title(html: str) -> str:
    if "<head" not in html.lower():
        html = html.replace("<html", "<html><head></head>", 1)

    if "<title>" in html.lower():
        start = html.lower().index("<title>")
        end = html.lower().index("</title>") + 8
        html = html[:start] + f"<title>{TITLE_REQUIRED}</title>" + html[end:]
    else:
        html = html.replace("<head>", f"<head><title>{TITLE_REQUIRED}</title>")

    return html


# -------------------------------------
# HEALTH CHECK
# -------------------------------------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# -------------------------------------
# HOMEPAGE
# -------------------------------------
@app.get("/")
def home():
    return send_from_directory(RESOURCES_DIR, "index.html")


# -------------------------------------
# WILDCARD ROUTE (FIXES 404 ON VERCEL)
# -------------------------------------
@app.get("/<path:path>")
def catch_all(path):
    return send_from_directory(RESOURCES_DIR, "index.html")


# -------------------------------------
# CREATE SPOTLIGHT
# -------------------------------------
@app.post("/api/spotlight")
def create_spotlight():

    user_id = "demo"

    if not allow(user_id, "/api/spotlight"):
        return jsonify({"error": "rate_limited"}), 429

    try:
        data = request.get_json(force=True)
        ticker = sanitize_ticker(data.get("ticker"))
        years = clamp_years(data.get("years"))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    attempts = []
    repair = None
    MAX_ATTEMPTS = 3

    for _ in range(MAX_ATTEMPTS):
        try:
            prompt = build_prompt(repair)
            html = gpt_generate_html(prompt, ticker, years)
        except Exception as e:
            return jsonify({"error": "gpt_failure", "detail": str(e)}), 500

        html = _enforce_required_title(html)
        ok, errs, meta = validate_html(html)

        attempts.append({"ok": ok, "errs": errs, "meta": meta})

        if ok:
            path, url = save_report(user_id, ticker, html)
            log_event("report_ok", ticker=ticker, years=years)
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        repair = f"Fix ONLY these issues: {errs}"

    log_event("report_fail", ticker=ticker, attempts=attempts)
    return jsonify({"error": "validation_failed", "attempts": attempts}), 422


# -------------------------------------
# HISTORY
# -------------------------------------
@app.get("/api/history")
def list_history():
    user_dir = REPORTS_ROOT / "demo"
    user_dir.mkdir(parents=True, exist_ok=True)

    items = []
    for f in user_dir.glob("DLENS_Spotlight_*.html"):
        items.append({
            "name": f.name,
            "url": f"/reports/demo/{f.name}",
            "mtime": f.stat().st_mtime
        })

    return jsonify(items)


# -------------------------------------
# SERVE REPORT FILES
# -------------------------------------
@app.get("/reports/<user>/<filename>")
def serve_report(user, filename):
    file_path = REPORTS_ROOT / user / filename
    if not file_path.exists():
        return "<h3>Not Found</h3>", 404
    return send_file(file_path)


# -------------------------------------
# VERCEL ASGI HANDLER
# -------------------------------------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
