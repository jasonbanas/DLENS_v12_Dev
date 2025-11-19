import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from spotlight import generate_spotlight

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static_reports"  # This serves report files
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "static_reports")


@app.route("/")
def home():
    return "<h2>DLENS Spotlight v12 API Running</h2>"


# -----------------------------------------------------
#  UI PAGE FOR SPOTLIGHT GENERATOR
# -----------------------------------------------------
@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight_ui.html")  # new UI file


# -----------------------------------------------------
#  API: Generate Spotlight
# -----------------------------------------------------
@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    data = request.get_json()
    ticker = data.get("ticker", "").upper().strip()
    horizon = int(data.get("horizon", 10))
    user_id = data.get("user_id", "")
    email_opt_in = data.get("email_opt_in", False)

    if ticker == "":
        return jsonify({"error": "Ticker is required"}), 400

    try:
        url = generate_spotlight(
            ticker=ticker,
            projection_years=horizon,
            user_id=user_id,
            email_opt_in=email_opt_in
        )
        return jsonify({"status": "success", "report_url": url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------
#  SERVE GENERATED REPORTS
# -----------------------------------------------------
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    file_path = os.path.join(REPORT_DIR, filename)

    if not os.path.exists(file_path):
        return "<h1>Report Not Found</h1>", 404

    return send_from_directory(REPORT_DIR, filename)


# -----------------------------------------------------
# RUN APP
# -----------------------------------------------------
if __name__ == "__main__":
    print("🔥 DLENS v12 Spotlight Backend running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
