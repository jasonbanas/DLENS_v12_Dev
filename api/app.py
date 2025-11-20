import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from spotlight import generate_spotlight

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static_reports"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "static_reports")


# ------------------------------------------
# HOME
# ------------------------------------------
@app.route("/")
def home():
    return "<h2>DLENS v12 Spotlight API Running</h2>"


# ------------------------------------------
# UI PAGES
# ------------------------------------------
@app.route("/spotlight")
def spotlight_ui():
    return render_template("spotlight_ui.html")


@app.route("/hunt")
def hunt_ui():
    return render_template("hunt.html")


# ------------------------------------------
# API — Generate Spotlight
# ------------------------------------------
@app.route("/api/spotlight", methods=["POST"])
def api_generate_spotlight():
    data = request.get_json()
    ticker = data.get("ticker", "").upper().strip()
    horizon = int(data.get("horizon", 1))

    if not ticker:
        return jsonify({"error": "Ticker symbol is required"}), 400

    # 🔥 Call your REAL spotlight generator
    report_url = generate_spotlight(ticker, horizon)

    return jsonify({
        "status": "success",
        "message": "Spotlight generated",
        "report_url": report_url
    })


# ------------------------------------------
# Serve generated report files
# ------------------------------------------
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    file_path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(file_path):
        return "<h1>Report Not Found</h1>", 404

    return send_from_directory(REPORT_DIR, filename)


# ------------------------------------------
# RUN SERVER
# ------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
