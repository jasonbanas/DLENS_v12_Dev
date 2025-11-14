from flask import Flask, request, jsonify, send_file
from pathlib import Path
import os

from services.generator import gpt_generate_html
from services.sanitize import sanitize_ticker, clamp_years
from services.validator import validate as validate_html
from services.storage import save_report
from services.ratelimit import allow
from services.obs import log_event
from services.rules_engine import build_prompt

TITLE_REQUIRED = "DLENS Disruptor Spotlight"

def enforce_title(html: str) -> str:
    if "<title>" not in html.lower():
        return html.replace("<head>", f"<head><title>{TITLE_REQUIRED}</title>")
    return html


# ---------------------------
# PATHS
# ---------------------------
API_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = API_DIR / "resources"
REPORTS_DIR = API_DIR.parent / "reports"

app = Flask(__name__, static_folder=str(RESOURCES_DIR))


# ---------------------------
# HEALTH
# ---------------------------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# ---------------------------
# FRONTEND (STATIC UI)
# ---------------------------
@app.get("/")
def home():
    index_path = RESOURCES_DIR / "index.html"
    if not index_path.exists():
        return "<h3>Missing index.html</h3>", 404
    return send_file(index_path)


# ---------------------------
# MAIN GENERATOR
# ---------------------------
@app.post("/api/spotlight")
def create_spotlight():

    # RATE LIMIT
    if not allow("demo", "spotlight"):
        return jsonify({"error": "rate_limited"}), 429

    # CHECK API KEY FIRST
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({
            "error": "missing_api_key",
            "message": "Please configure OPENAI_API_KEY"
        }), 500

    # READ JSON BODY
    try:
        data = request.get_json(force=True)
        ticker = sanitize_ticker(data.get("ticker"))
        years = clamp_years(data.get("years"))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    attempts = []
    repair = None

    for _ in range(3):
        prompt = build_prompt(repair)

        try:
            html = gpt_generate_html(prompt, ticker, years)
        except Exception as e:
            return jsonify({"error": "gpt_error", "detail": str(e)}), 500

        html = enforce_title(html)
        ok, errs, meta = validate_html(html)
        attempts.append({"ok": ok, "errs": errs, "meta": meta})

        if ok:
            file_path, url = save_report("demo", ticker, html)
            log_event("report_success", ticker=ticker)
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        repair = f"Fix ONLY these problems: {errs}"

    log_event("report_fail", ticker=ticker)
    return jsonify({"error": "validation_failed", "attempts": attempts}), 422


# ---------------------------
# SERVE REPORTS
# ---------------------------
@app.get("/reports/<user>/<filename>")
def serve_report(user, filename):
    path = REPORTS_DIR / user / filename
    if not path.exists():
        return "<h3>Report Not Found</h3>", 404
    return send_file(path)


# ASGI FOR VERCEL
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app


if __name__ == "__main__":
    app.run(port=8000)
