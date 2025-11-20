import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from spotlight import generate_spotlight

app = Flask(__name__, template_folder="templates")


# ============================
# HOME PAGE (API STATUS)
# ============================
@app.route("/")
def home():
    return "DLENS v12 Spotlight API Running"


# ============================
# SPOTLIGHT UI PAGE
# ============================
@app.route("/spotlight")
def ui():
    return render_template("spotlight_ui.html")


# ============================
# API: GENERATE SPOTLIGHT
# ============================
@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        ticker = data.get("ticker", "").upper().strip()
        horizon = int(data.get("horizon", 1))

        if ticker == "":
            return jsonify({"error": "Ticker is required"}), 400

        # Call generator
        url = generate_spotlight(
            ticker=ticker,
            projection_years=horizon,
            user_id="guest",
            email_opt_in=False
        )

        return jsonify({"url": url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================
# SERVE GENERATED HTML REPORTS
# ============================
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory("static_reports", filename)


# ============================
# RENDER ENTRY POINT
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
