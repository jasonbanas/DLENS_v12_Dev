from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
import os, re, traceback, sys, importlib
from dotenv import load_dotenv
load_dotenv()

TITLE_REQUIRED = "DLENS Disruptor Spotlight"

def _enforce_required_title(html: str) -> str:
    import re
    if "<head" not in html.lower():
        html = html.replace("<html", "<html><head></head>", 1)
    if re.search(r"(?is)<title>.*?</title>", html):
        html = re.sub(r"(?is)<title>.*?</title>", f"<title>{TITLE_REQUIRED}</title>", html, count=1)
    else:
        html = re.sub(r"(?is)<head([^>]*)>", rf"<head\1><title>{TITLE_REQUIRED}</title>", html, count=1)
    return html

# ---------- PATH SETUP ----------
API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent

STATIC_DIR = ROOT_DIR / "static"
TEMPLATE_ROOT = API_DIR / "dlens_app"
REPORTS_ROOT = ROOT_DIR / "reports"
SERVICES_DIR = API_DIR / "services"

# FIXED: Your index.html is under core/resources
RESOURCES_DIR = ROOT_DIR / "core" / "resources"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
    template_folder=str(TEMPLATE_ROOT),
)

@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})

# ---------- BASIC SANITIZERS ----------
def sanitize_ticker(v: str) -> str:
    if not v: raise ValueError("Ticker required")
    v = v.upper().strip()
    if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
        raise ValueError("Invalid ticker format")
    return v

def clamp_years(v) -> int:
    try: n = int(v)
    except: n = 6
    return max(1, min(20, n))

# ---------- MAIN SPOTLIGHT ENDPOINT ----------
@app.post("/api/spotlight")
def create_spotlight():
    try:
        payload = request.get_json(force=True) or {}
        ticker = sanitize_ticker(payload.get("ticker"))
        years = clamp_years(payload.get("years", 6))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    try:
        base = Path(__file__).resolve().parent / "services"
        gen_path = base / "generator.py"
        val_path = base / "validator.py"

        spec_gen = importlib.util.spec_from_file_location("generator", gen_path)
        spec_val = importlib.util.spec_from_file_location("validator", val_path)

        generator = importlib.util.module_from_spec(spec_gen)
        validator = importlib.util.module_from_spec(spec_val)

        spec_gen.loader.exec_module(generator)
        spec_val.loader.exec_module(validator)

        gpt_generate_html = generator.gpt_generate_html
        validate_html = validator.validate
    except Exception as e:
        return jsonify({"error": "server_misconfigured", "detail": str(e)}), 500

    # Try generation 3x
    for _ in range(3):
        try:
            html = gpt_generate_html(f"Generate DLENS spotlight for {ticker}", ticker, years)
        except Exception as e:
            return jsonify({"error": "upstream_unreachable", "detail": str(e)}), 502

        html = _enforce_required_title(html)

        ok, errs, meta = validate_html(html)
        if ok:
            user_id = "demo"
            folder = REPORTS_ROOT / user_id
            folder.mkdir(parents=True, exist_ok=True)

            filename = f"DLENS_Spotlight_{ticker}.html"
            path = folder / filename
            path.write_text(html, encoding="utf-8")

            return jsonify({
                "url": f"/reports/{user_id}/{filename}",
                "meta": meta
            }), 201

    return jsonify({"error": "validation_failed", "details": errs}), 422

# ---------- HOMEPAGE ----------
@app.get("/")
def home():
    try:
        return send_from_directory(str(RESOURCES_DIR), "index.html")
    except Exception as e:
        return f"<pre>Error loading UI\n{e}\nRESOURCES_DIR={RESOURCES_DIR}</pre>", 500

# ---------- STATIC REPORTS ----------
@app.route("/reports/<user_id>/<path:filename>")
def serve_report(user_id, filename):
    fpath = REPORTS_ROOT / user_id / filename
    if not fpath.exists():
        return ("<h3>Not Found</h3>", 404)
    return send_file(fpath, mimetype="text/html")

# ---------- ASGI WRAP ----------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
