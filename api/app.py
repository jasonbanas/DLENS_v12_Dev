from pathlib import Path
from flask import Flask, request, jsonify, send_file
import os

# ---------------------------------------------------
# NO BROKEN IMPORTS. ALL CUSTOM MODULES REMOVED.
# ---------------------------------------------------

app = Flask(__name__)

# Path to index.html
BASE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = BASE_DIR / "resources"


# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# ---------------------------
# HOME PAGE UI
# ---------------------------
@app.get("/")
def home():
    index_file = RESOURCES_DIR / "index.html"

    if not index_file.exists():
        return f"index.html NOT FOUND in {index_file}", 404

    return send_file(index_file)


# ---------------------------
# SPOTLIGHT (STATIC DUMMY RESPONSE)
# ---------------------------
@app.post("/api/spotlight")
def spotlight():
    """
    TEST VERSION ONLY
    This ensures your API works WITHOUT calling GPT,
    WITHOUT calling validator,
    WITHOUT calling rules_engine.
    """

    data = request.get_json(silent=True) or {}

    return jsonify({
        "url": "https://example.com/report.html",
        "input": data,
        "status": "OK (dummy response)"
    }), 201


# ---------------------------
# ASGI adapter (Vercel)
# ---------------------------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app


if __name__ == "__main__":
    app.run(port=8000, debug=True)
