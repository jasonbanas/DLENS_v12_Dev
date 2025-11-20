import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from spotlight import generate_spotlight

app = Flask(__name__, static_folder="static_reports", template_folder="templates")

# ----------------------------
# HOME
# ----------------------------
@app.route("/")
def home():
    return "DLENS v12 Spotlight API Running"

# ----------------------------
# UI PAGE
# ----------------------------
@app.route("/spotlight")
def spotlight_ui():
    return render_template("spotlight_ui.html")

# ----------------------------
# GENERATE SPOTLIGHT REPORT
# ----------------------------
@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    try:
        data = request.get_json()
        ticker = data.get("ticker", "").upper()
        years = data.get("years", 1)

        report_url = generate_spotlight(ticker, years)

        return jsonify({"status": "success", "url": report_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------
# SERVE GENERATED REPORTS
# ----------------------------
@app.route("/api/reports/<filename>")
def serve_report(filename):
    return send_from_directory("static_reports", filename)

# ----------------------------
# PRODUCTION ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  
    app.run(host="0.0.0.0", port=port)
