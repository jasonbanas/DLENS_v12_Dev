from flask import Flask, request, jsonify, send_file
from pathlib import Path
from spotlight import generate_spotlight

app = Flask(__name__)

# correct path to /api/static_reports/
BASE_DIR = Path(__file__).resolve().parent
STATIC_REPORTS = BASE_DIR / "static_reports"


@app.get("/")
def home():
    return send_file(BASE_DIR / "resources" / "index.html")


@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})


@app.post("/api/spotlight")
def api_spotlight():
    data = request.get_json()

    ticker = data.get("query", "").strip()
    years = int(data.get("years", 10))

    if not ticker:
        return jsonify({"error": "ticker_missing"}), 400

    url = generate_spotlight(ticker, years, "demo", False)

    return jsonify({"url": url})


@app.get("/api/reports/<filename>")
def serve_report(filename):
    file_path = STATIC_REPORTS / filename

    if not file_path.exists():
        return "<h1>Report Not Found</h1>", 404

    return send_file(file_path)


if __name__ == "__main__":
    app.run(debug=True)
