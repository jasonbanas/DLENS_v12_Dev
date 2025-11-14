# api/app.py
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
import os, re, traceback, sys, importlib
from dotenv import load_dotenv
load_dotenv()

TITLE_REQUIRED = "DLENS Disruptor Spotlight"

def _enforce_required_title(html: str) -> str:
    import re
    if "<head" not in html.lower():
        html = html.replace("<html", "<html><head></head>", 1)
    if re.search(r"(?is)<title>.*?</title>", html):
        html = re.sub(r"(?is)<title>.*?</title>",
                      f"<title>{TITLE_REQUIRED}</title>", html, count=1)
    else:
        html = re.sub(r"(?is)<head([^>]*)>",
                      rf"<head\1><title>{TITLE_REQUIRED}</title>", html, count=1)
    return html


# -------- PATHS --------
API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent

RESOURCES_DIR = API_DIR / "resources"     # FIXED PATH
REPORTS_ROOT = ROOT_DIR / "reports"
SERVICES_DIR = API_DIR / "services"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

app = Flask(
    __name__,
    static_folder=None,
    template_folder=None
)


# ---------- HEALTH CHECK ----------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# ---------- SANITIZE ----------
def sanitize_ticker(v: str) -> str:
    v = (v or "").upper().strip()
    if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
        raise ValueError("Invalid ticker format")
    return v


def clamp_years(v) -> int:
    try:
        n = int(v)
    except:
        n = 6
    return max(1, min(20, n))


# ---------- LOAD GENERATOR/STUB ----------
try:
    from .services.generator import gpt_generate_html
except:
    # Stub fallback
    def gpt_generate_html(prompt, ticker, years):
        return f"""
        <html><head><title>{TITLE_REQUIRED}</title></head>
        <body><h1>DLENS STUB REPORT</h1><p>{ticker}</p></body></html>
        """


# ---------- LOAD VALIDATOR/STUB ----------
try:
    from .services.validator import validate
except:
    def validate(html):
        return True, [], {"stub": True}


# ---------- SAVE REPORT ----------
def save_report(user_id: str, ticker: str, html: str):
    folder = REPORTS_ROOT / user_id
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"DLENS_Spotlight_{ticker}.html"
    file_path = folder / filename
    file_path.write_text(html, encoding="utf-8")
    return str(file_path), f"/reports/{user_id}/{filename}"


# ---------- SPOTLIGHT ----------
@app.post("/api/spotlight")
def create_spotlight():
    try:
        payload = request.get_json(force=True) or {}
        ticker = sanitize_ticker(payload.get("ticker"))
        years = clamp_years(payload.get("years"))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    html = gpt_generate_html("prompt", ticker, years)
    html = _enforce_required_title(html)

    ok, errs, meta = validate(html)
    if not ok:
        return jsonify({"error": "validation_failed", "details": errs}), 422

    path, url = save_report("demo", ticker, html)
    return jsonify({"url": url, "meta": meta}), 201


# ---------- SERVE UI ----------
@app.get("/")
def serve_index():
    try:
        return send_from_directory(str(RESOURCES_DIR), "index.html")
    except Exception as e:
        return (f"Error loading UI<br>{e}<br>RESOURCES_DIR={RESOURCES_DIR}", 404)


# ---------- REPORTS ----------
@app.get("/reports/<user_id>/<path:filename>")
def serve_report(user_id, filename):
    file_path = REPORTS_ROOT / user_id / filename
    if not file_path.exists():
        return "<h3>Not Found</h3>", 404
    return send_file(file_path, mimetype="text/html")


# ASGI Wrapper
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app
