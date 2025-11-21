from flask import Flask, render_template, request, jsonify, send_from_directory
from api.spotlight import generate_spotlight_report
import os

app = Flask(__name__, static_folder="static_reports", template_folder="templates")


# ----------------------------------------
# HOME PAGE (UI)
# ----------------------------------------
@app.route("/")
def home():
    return render_template("spotlight_ui.html")

@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight_ui.html")


# ----------------------------------------
# API: Generate Spotlight (JSON only)
# ----------------------------------------
@app.route("/api/spotlight", methods=["POST"])
def spotlight_api():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    ticker = data.get("ticker")
    horizon = data.get("horizon")

    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400
    if not horizon:
        return jsonify({"error": "Missing horizon"}), 400

    # Generate HTML report
    html_file = generate_spotlight_report(ticker, horizon)

    return jsonify({"html": html_file})


# ----------------------------------------
# Serve Generated HTML Files
# ----------------------------------------
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory("static_reports", filename)


# ----------------------------------------
# Local Debug (Render uses Gunicorn)
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
