# api/app.py

from flask import Flask, jsonify, request, render_template, send_from_directory
from api.spotlight import save_spotlight_report

app = Flask(__name__, static_folder="static_reports", template_folder="../templates")


@app.route("/")
def home():
    return render_template("spotlight_ui.html")


# SAVE-ONLY ENDPOINT
@app.route("/api/spotlight/save", methods=["POST"])
def save_spotlight():
    data = request.json

    ticker = data.get("ticker")
    horizon = data.get("horizon")
    html_content = data.get("html")

    if not ticker or not horizon or not html_content:
        return jsonify({"error": "Missing fields"}), 400

    url = save_spotlight_report(ticker, horizon, html_content)
    return jsonify({"url": url})


@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory("static_reports", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
