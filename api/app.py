# api/app.py
from pathlib import Path
from flask import Flask, request, jsonify
import os  # NEW

# Static setup -> project-root/static
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

# Health
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})

# Reports blueprint (optional fallback; ok to skip during early dev)
try:
    from .routes.reports import bp as reports_bp
    app.register_blueprint(reports_bp)
except Exception as e:
    app.logger.warning(f"[DLENS] reports blueprint not registered: {e}")

# Prompt builder (fallback ok)
try:
    from .rules_engine import build_prompt
except Exception as e:
    app.logger.warning(f"[DLENS] rules_engine missing, using stub: {e}")
    def build_prompt(extra_hints: str | None = None) -> str:
        base = "<html><body><h1>DLENS Stub Prompt</h1></body></html>"
        return base + (f"\n<!-- Hints -->\n{extra_hints}" if extra_hints else "")

# Storage + logging (fallback ok)
try:
    from .services.storage import save_report
except Exception as e:
    app.logger.warning(f"[DLENS] storage missing, using stub saver: {e}")
    def save_report(user_id: str, ticker: str, html: str):
        return (
            f"/dev/null/{user_id}/DLENS_Spotlight_{ticker}.html",
            f"/static/reports/{user_id}/DLENS_Spotlight_{ticker}.html",
        )

try:
    from .services.obs import log_event
except Exception as e:
    app.logger.warning(f"[DLENS] obs missing, using stub logger: {e}")
    def log_event(event, **kw):
        app.logger.info({"event": event, **kw})

# Input guards (fallback ok)
try:
    from .services.sanitize import sanitize_ticker, clamp_years
except Exception as e:
    app.logger.warning(f"[DLENS] sanitize missing, using basic guards: {e}")
    import re
    def sanitize_ticker(v: str) -> str:
        v = (v or "").upper()
        if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
            raise ValueError("Invalid ticker format")
        return v
    def clamp_years(v) -> int:
        try:
            n = int(v)
        except Exception:
            n = 6
        return max(1, min(20, n))

# Rate limit (fallback ok)
try:
    from .services.ratelimit import allow
except Exception as e:
    app.logger.warning(f"[DLENS] ratelimit missing, allowing all: {e}")
    def allow(user_id: str, route: str) -> bool:
        return True

# --- NEW: flag to enable/disable rate limiting at runtime
RATE_ENABLED = os.getenv("RATE_ENABLED", "true").lower() == "true"  # NEW

# IMPORTANT: real generator + validator (NO fallbacks)
from .services.generator import gpt_generate_html          # <- must exist
from .services.validator import validate as validate_html  # <- must exist

MAX_ATTEMPTS = 3

def _get_user_id():
    return getattr(getattr(request, "user", None), "id", "demo")

@app.post("/api/spotlight")
def create_spotlight():
    user_id = _get_user_id()

    # Only enforce limiter if RATE_ENABLED=true
    if RATE_ENABLED and not allow(user_id, "/api/spotlight"):  # NEW
        return jsonify({"error": "rate_limited", "detail": "Too many requests"}), 429

    try:
        payload = request.get_json(force=True) or {}
        ticker = sanitize_ticker(payload.get("ticker"))
        years = clamp_years(payload.get("years", 6))
    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    attempts = []
    repair_hints = None

    for _ in range(MAX_ATTEMPTS):
        try:
            html = gpt_generate_html(
                prompt=build_prompt(repair_hints),
                ticker=ticker,
                years=years
            )
        except Exception as e:
            # Upstream/network/auth issues -> surface clearly
            return jsonify({"error": "upstream_unreachable", "detail": str(e)}), 502

        ok, errs, meta = validate_html(html)
        attempts.append({"ok": bool(ok), "errs": errs, "meta": meta})

        if ok:
            path, url = save_report(user_id, ticker, html)
            log_event(
                "report_ok",
                user_id=user_id,
                ticker=ticker,
                years=years,
                path=str(path),
                meta=meta,
            )
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        # auto-heal hint for next pass
        repair_hints = f"Fix ONLY these issues: {errs}. Keep all passing sections verbatim."

    # Exhausted attempts -> 422 per contract
    last_errs = attempts[-1]["errs"] if attempts else ["no_attempts"]
    log_event("report_fail", user_id=user_id, ticker=ticker, years=years, errs=last_errs)
    return jsonify({
        "error": "validation_failed",
        "details": last_errs,
        "attempts": attempts
    }), 422

# Minimal landing page (unique endpoint name to avoid collisions)
@app.get("/", endpoint="home")
def home():
    return (
        """<!doctype html><html><body style="font-family:sans-serif">
        <h1>DLENS Spotlight API</h1>
        <ul>
          <li><a href="/api/ping">/api/ping</a></li>
          <li>POST /api/spotlight (body: {"ticker":"TSLA","years":6})</li>
          <li><a href="/api/reports?user_id=demo">/api/reports?user_id=demo</a></li>
        </ul>
        </body></html>""",
        200,
        {"Content-Type": "text/html"},
    )

# ASGI wrapper so Uvicorn can run this Flask app (api.app:asgi_app)
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except Exception:
    asgi_app = app
