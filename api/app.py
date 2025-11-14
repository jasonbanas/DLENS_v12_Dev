from pathlib import Path
from flask import Flask, request, jsonify, send_file
import os

# ---------------------------
# FIXED IMPORTS
# ---------------------------
from services.generator import gpt_generate_html
from services.validator import validate as validate_html
from services.sanitize import sanitize_ticker, clamp_years
from services.storage import save_report
from services.obs import log_event
from services.ratelimit import allow
from services.rules_engine import build_prompt

TITLE_REQUIRED = "DLENS Disruptor Spotlight"


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


# ---------------------------
# FIXED PATHS
# ---------------------------
API_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = API_DIR / "resources"
REPORTS_ROOT = API_DIR.parent / "reports"

app = Flask(
    __name__,
    static_folder=str(RESOURCES_DIR),
    static_url_path="/static"
)


# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/")
def home():
    index_path = RESOURCES_DIR / "index.html"
    if not index_path.exists():
        return "<h3>index.html missing</h3>", 404
    return send_file(index_path)


# ---------------------------
# GENERATE SPOTLIGHT
# ---------------------------
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

    repair = None
    attempts = []

    for _ in range(3):
        try:
            prompt = build_prompt(repair)
            html = gpt_generate_html(prompt, ticker, years)
        except Exception as e:
            return jsonify({"error": "gpt_failure", "detail": str(e)}), 500

        html = _enforce_required_title(html)

        ok, errs, meta = validate_html(html)
        attempts.append({"ok": ok, "errs": errs, "meta": meta})

        if ok:
            file_path, url = save_report("demo", ticker, html)
            log_event("report_ok", ticker=ticker, years=years)
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        repair = f"Fix ONLY these: {errs}"

    log_event("report_fail", ticker=ticker, attempts=attempts)
    return jsonify({"error": "validation_failed", "attempts": attempts}), 422


# ---------------------------
# API TO SERVE REPORT
# ---------------------------
@app.get("/reports/<user>/<filename>")
def serve_report(user, filename):
    file_path = REPORTS_ROOT / user / filename
    if not file_path.exists():
        return "<h3>Not Found</h3>", 404
    return send_file(file_path)


# ---------------------------
# ASGI for Vercel
# ---------------------------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app


# Local debug
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
