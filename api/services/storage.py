from flask import Flask, request, jsonify, send_file
from pathlib import Path
import os

app = Flask(__name__)

API_DIR = Path(__file__).resolve().parent
RESOURCES = API_DIR / "resources"
REPORTS = API_DIR / "reports"
REPORTS.mkdir(exist_ok=True)

@app.get("/api/ping")
def ping():
    return jsonify({"ok": True})

@app.get("/")
def home():
    index = RESOURCES / "index.html"
    return send_file(index)

@app.post("/api/spotlight")
def spotlight():
    data = request.get_json()
    ticker = data.get("ticker", "UNKNOWN")
    years = data.get("years", 10)

    # temporary HTML output
    html = f"<html><body><h1>Report for {ticker}</h1><p>Years: {years}</p></body></html>"

    out = REPORTS / f"{ticker}.html"
    out.write_text(html, encoding="utf-8")

    return jsonify({"url": f"/api/reports/{ticker}.html"})

@app.get("/api/reports/<filename>")
def reports(filename):
    fp = REPORTS / filename
    return send_file(fp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
