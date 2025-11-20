from flask import Flask, request, jsonify, render_template, send_from_directory
from spotlight import generate_spotlight
import os

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static_reports"  # Serve generated reports
)

# ===========================
# HOME PAGE (UI)
# ===========================
@app.route("/")
def index():
    return render_template("spotlight_ui.html")


# ===========================
# OPTIONAL UI ROUTE
# ===========================
@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight_ui.html")


# ===========================
# API ENDPOINT FOR SPOTLIGHT
# ===========================
@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    data = request.get_json()

    ticker = data.get("ticker")
    years = data.get("years")

    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    try:
        years = int(years)
    except:
        years = 1

    # Generate the report
    url = generate_spotlight(ticker, years)

    return jsonify({"url": url})


# ===========================
# SERVE GENERATED REPORT FILES
# ===========================
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    reports_dir = os.path.join(os.getcwd(), "api/static_reports")
    return send_from_directory(reports_dir, filename)


# ===========================
# RUN LOCAL DEV
# ===========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🔥 DLENS Spotlight running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
