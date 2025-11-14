# api/app.py
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
RESOURCES_DIR = API_DIR / "resources"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
    template_folder=str(TEMPLATE_ROOT),
)

# ---------- HEALTH CHECK ----------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})

# ---------- OPTIONAL BLUEPRINTS ----------
try:
    from .routes.reports import bp as reports_bp
    app.register_blueprint(reports_bp)
except Exception as e:
    app.logger.warning(f"[DLENS] reports blueprint not registered: {e}")

# ---------- OPTIONAL SERVICES (SAFE FALLBACKS) ----------
try:
    from .rules_engine import build_prompt
except Exception as e:
    app.logger.warning(f"[DLENS] rules_engine missing, using stub: {e}")
    def build_prompt(extra_hints: str | None = None) -> str:
        base = "<html><body><h1>DLENS Stub Prompt</h1></body></html>"
        return base + (f"\n<!-- Hints -->\n{extra_hints}" if extra_hints else "")

try:
    from .services.storage import save_report
except Exception as e:
    app.logger.warning(f"[DLENS] storage missing, using stub saver: {e}")
    def save_report(user_id: str, ticker: str, html: str):
        folder = REPORTS_ROOT / user_id
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"DLENS_Spotlight_{ticker}_ID_251110_GoldStandard_v12.html"
        file_path = folder / filename
        file_path.write_text(html, encoding="utf-8")
        return str(file_path), f"/reports/{user_id}/{filename}"

try:
    from .services.obs import log_event
except Exception as e:
    app.logger.warning(f"[DLENS] obs missing, using stub logger: {e}")
    def log_event(event, **kw):
        app.logger.info({"event": event, **kw})

try:
    from .services.sanitize import sanitize_ticker, clamp_years
except Exception as e:
    app.logger.warning(f"[DLENS] sanitize missing, using basic guards: {e}")
    def sanitize_ticker(v: str) -> str:
        v = (v or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
            raise ValueError("Invalid ticker format")
        return v
    def clamp_years(v) -> int:
        try:
            n = int(v)
        except Exception:
            n = 6
        return max(1, min(20, n))

try:
    from .services.ratelimit import allow
except Exception as e:
    app.logger.warning(f"[DLENS] ratelimit missing, allowing all: {e}")
    def allow(user_id: str, route: str) -> bool:
        return True

# ---------- CONFIG ----------
RATE_ENABLED = os.getenv("RATE_ENABLED", "true").lower() == "true"
MAX_ATTEMPTS = 3

def _get_user_id():
    return getattr(getattr(request, "user", None), "id", "demo")

# ---------- CREATE SPOTLIGHT ----------
@app.post("/api/spotlight")
def create_spotlight():
    user_id = _get_user_id()

    if RATE_ENABLED and not allow(user_id, "/api/spotlight"):
        return jsonify({"error": "rate_limited", "detail": "Too many requests"}), 429

    try:
        payload = request.get_json(force=True) or {}
        ticker = sanitize_ticker(payload.get("ticker"))
        years = clamp_years(payload.get("years", 6))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    # --------- robust import for generator + validator ---------
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

        app.logger.info("[DLENS] generator + validator dynamically loaded ✅")
    except Exception as e:
        app.logger.error(f"[DLENS] dynamic import failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "error": "server_misconfigured",
            "detail": "generator/validator not available"
        }), 500

    attempts, repair_hints = [], None
    for _ in range(MAX_ATTEMPTS):
        try:
            html = gpt_generate_html(build_prompt(repair_hints), ticker, years)
        except Exception as e:
            app.logger.error(f"[DLENS] generator runtime error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": "upstream_unreachable", "detail": str(e)}), 502

        html = _enforce_required_title(html)
        ok, errs, meta = validate_html(html)
        attempts.append({"ok": bool(ok), "errs": errs, "meta": meta})

        if ok:
            path, url = save_report(user_id, ticker, html)
            log_event("report_ok", user_id=user_id, ticker=ticker, years=years, path=str(path), meta=meta)
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        repair_hints = f"Fix ONLY these issues: {errs}. Keep all passing sections verbatim."

    last_errs = attempts[-1]["errs"] if attempts else ["no_attempts"]
    log_event("report_fail", user_id=user_id, ticker=ticker, years=years, errs=last_errs)
    return jsonify({"error": "validation_failed", "details": last_errs, "attempts": attempts}), 422

# ---------- HOME / UI ----------
@app.get("/", endpoint="home")
def home():
    try:
        return send_from_directory(str(RESOURCES_DIR), "index.html")
    except Exception as e:
        app.logger.error(f"[DLENS] template render failed: {e}\n{traceback.format_exc()}")
        return (f"<pre>Template error: {e}\n\nRESOURCES_DIR={RESOURCES_DIR}</pre>", 500, {"Content-Type": "text/html"})

# ---------- REPORTS SERVING ----------
@app.route("/reports/<user_id>/<path:filename>")
def serve_report(user_id, filename):
    target_dir = REPORTS_ROOT / user_id
    file_path = target_dir / filename
    app.logger.info(f"[DLENS] serve_report → {file_path}")

    if not file_path.exists():
        return (f"<h3>Not Found</h3><pre>{file_path}</pre>", 404, {"Content-Type": "text/html"})
    return send_file(file_path, mimetype="text/html")

# ---------- REPORT HISTORY ----------
@app.get("/api/history")
def list_reports():
    user_id = _get_user_id()
    user_dir = REPORTS_ROOT / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for file in sorted(user_dir.glob("DLENS_Spotlight_*.html"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            meta = {"name": file.name, "url": f"/reports/{user_id}/{file.name}", "mtime": file.stat().st_mtime}
            files.append(meta)
        except Exception as e:
            app.logger.warning(f"[DLENS] failed to read report {file}: {e}")
    return jsonify(files)

# ---------- AI INSIGHT SUMMARY ----------
@app.post("/api/insight")
def generate_insight():
    try:
        data = request.get_json(force=True)
        ticker = data.get("ticker", "UNKNOWN")
        years = data.get("years", "N/A")
        user_id = _get_user_id()

        user_dir = REPORTS_ROOT / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        pattern = f"DLENS_Spotlight_{ticker}_*.html"
        matches = sorted(user_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
        if not matches:
            matches = sorted(user_dir.glob("DLENS_Spotlight_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not matches:
            return jsonify({"ok": False, "error": f"No report found for ticker {ticker}"}), 404

        file_path = matches[0]
        html = file_path.read_text(encoding="utf-8")

        summary = []
        if "Founder" in html:
            summary.append("Mentions strong founder execution potential.")
        if "Risk" in html:
            summary.append("Includes a detailed risk assessment section.")
        if "Peer" in html:
            summary.append("Compares performance with key industry peers.")
        if "CSP" in html:
            summary.append("Integrates multi-source financial consistency (CSP).")
        if "DUU" in html:
            summary.append("Contains DUU (Disruptor Unique Understanding) overview.")
        if "Feasibility" in html:
            summary.append("Covers technical and commercial feasibility.")
        if not summary:
            summary = ["Basic HTML structure detected, but no specific insight tags found."]

        insight_text = " ".join(summary)
        return jsonify({"ok": True, "ticker": ticker, "years": years, "insight": insight_text, "source": str(file_path)})

    except Exception as e:
        app.logger.error(f"[DLENS] insight generation failed: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ---------- ASGI WRAPPER ----------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except Exception as e:
    print(f"[DLENS] ASGI setup fallback: {e}")
    asgi_app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
