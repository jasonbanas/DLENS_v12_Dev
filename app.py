from flask import Flask, render_template, request, jsonify
from api.spotlight import generate_spotlight_report

app = Flask(__name__)


# ----------------------------------------
# HOME PAGE (UI)
# ----------------------------------------
# When user visits "/", show the Spotlight Generator UI
@app.route("/")
def home():
    return render_template("spotlight_ui.html")


# Optional path /spotlight to also open the UI
@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight_ui.html")


# ----------------------------------------
# API: Generate Spotlight
# ----------------------------------------
@app.route("/api/spotlight", methods=["POST"])
def spotlight_api():
    data = request.json
    ticker = data.get("ticker")
    horizon = data.get("horizon")

    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    # Generate the DLENS v12 Gold HTML
    html_report = generate_spotlight_report(ticker, horizon)

    return jsonify({"html": html_report})


# ----------------------------------------
# Required for local debugging (Gunicorn is used in Render)
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
