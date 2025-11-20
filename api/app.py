from flask import Flask, request, jsonify, render_template, send_from_directory
from spotlight import generate_spotlight
import os

app = Flask(__name__, template_folder="templates", static_folder="static_reports")

# ------------------------
# FRONT-END PAGES
# ------------------------

@app.route("/")
def home():
    return render_template("spotlight_ui.html")

@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight_ui.html")


# ------------------------
# API FOR SPOTLIGHT GENERATION
# ------------------------
@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    data = request.get_json()

    ticker = data.get("ticker")
    horizon = data.get("projection_years")
    user_id = data.get("user_id", "guest")
    email_opt_in = data.get("email_opt_in", False)

    url = generate_spotlight(ticker, horizon, user_id, email_opt_in)

    return jsonify({"url": url})


# ------------------------
# SERVE STATIC REPORT FILES
# ------------------------
@app.route("/api/reports/<path:filename>")
def reports(filename):
    return send_from_directory("static_reports", filename)


# ------------------------
# PORT BIND FOR RENDER
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
