from flask import Flask, request, send_from_directory, jsonify
from spotlight import generate_spotlight, REPORT_DIR
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "<h2>DLENS v12 Spotlight Generator — Running</h2>"

@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    data = request.get_json()

    ticker = data.get("ticker")
    years = data.get("projection_years")
    user_id = data.get("user_id", "none")
    email_opt = data.get("email_opt_in", False)

    if not ticker or not years:
        return jsonify({"error": "Missing ticker or projection_years"}), 400

    url = generate_spotlight(ticker, years, user_id, email_opt)

    return jsonify({"url": url})

@app.route("/api/reports/<path:filename>")
def report_get(filename):
    return send_from_directory(REPORT_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
