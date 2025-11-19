import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------------------------------------------
#  FLASK APP CONFIG
# -------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder="templates",       # spotlight.html / hunt.html UI
    static_folder="static_reports"     # for /api/reports/
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "static_reports")

# -------------------------------------------------------------------
#  ROOT → DEFAULT TO SPOTLIGHT UI
# -------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("spotlight.html")     # <<< THIS FIXES YOUR ISSUE

# -------------------------------------------------------------------
#  FRONTEND PAGES
# -------------------------------------------------------------------
@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight.html")

@app.route("/hunt")
def hunt_page():
    return render_template("hunt.html")

# -------------------------------------------------------------------
#  SPOTLIGHT API
# -------------------------------------------------------------------
@app.route("/api/spotlight", methods=["POST"])
def api_generate_spotlight():

    data = request.get_json()
    ticker = data.get("ticker", "").upper().strip()
    horizon = int(data.get("horizon", 6))

    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    mock_report_name = f"DLENS_Spotlight_{ticker}.html"
    mock_path = os.path.join(REPORT_DIR, mock_report_name)

    if not os.path.exists(mock_path):
        return jsonify({
            "status": "error",
            "message": f"Mock report for {ticker} not found in static_reports/"
        }), 404

    return jsonify({
        "status": "success",
        "report_url": f"/api/reports/{mock_report_name}"
    })

# -------------------------------------------------------------------
#  DISRUPTOR HUNT API
# -------------------------------------------------------------------
@app.route("/api/hunt", methods=["POST"])
def api_disruptor_hunt():

    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    return jsonify({
        "status": "success",
        "results": [
            {
                "ticker": "AAPL",
                "company": "Apple Inc.",
                "score": 9.1,
                "projection": "$350",
                "summary": "Apple is a leading innovator in AI and device ecosystems.",
                "spotlight_url": "/api/reports/DLENS_Spotlight_AAPL.html"
            },
            {
                "ticker": "TSLA",
                "company": "Tesla, Inc.",
                "score": 9.4,
                "projection": "$1400",
                "summary": "Tesla leads robotics, AI, autonomy, and energy ecosystems.",
                "spotlight_url": "/api/reports/DLENS_Spotlight_TSLA.html"
            }
        ]
    })

# -------------------------------------------------------------------
#  SERVE STATIC SPOTLIGHT HTML FILES
# -------------------------------------------------------------------
@app.route("/api/reports/<path:filename>")
def serve_report(filename):

    file_path = os.path.join(REPORT_DIR, filename)

    if not os.path.exists(file_path):
        return "<h1>Report Not Found</h1>", 404

    return send_from_directory(REPORT_DIR, filename)

# -------------------------------------------------------------------
#  RUN SERVER
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("🔥 DLENS v12 Spotlight Backend running at: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
