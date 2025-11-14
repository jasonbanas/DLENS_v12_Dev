from pathlib import Path
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = BASE_DIR / "resources"


# -----------------------------------------
# HEALTH CHECK
# -----------------------------------------
@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


# -----------------------------------------
# FRONTEND UI
# -----------------------------------------
@app.get("/")
def home():
    index = RESOURCES_DIR / "index.html"

    if not index.exists():
        return f"index.html NOT FOUND in {index}", 404

    return send_file(index)


# -----------------------------------------
# SPOTLIGHT (dummy for now)
# -----------------------------------------
@app.post("/api/spotlight")
def create_spotlight():
    data = request.get_json(silent=True) or {}

    return jsonify({
        "status": "success",
        "message": "Working API skeleton",
        "input": data
    }), 201


# -----------------------------------------
# ASGI SUPPORT FOR VERCEL
# -----------------------------------------
try:
    from asgiref.wsgi import WsgiToAsgi
    asgi_app = WsgiToAsgi(app)
except:
    asgi_app = app


# Local run
if __name__ == "__main__":
    app.run(port=8000, debug=True)
