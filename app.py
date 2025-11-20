from flask import Flask, render_template, request, jsonify
from api.spotlight import generate_spotlight

app = Flask(__name__, template_folder="api/templates")

@app.route("/")
def home():
    return render_template("spotlight_ui.html")

@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    data = request.json
    ticker = data.get("ticker")
    horizon = data.get("horizon")

    if not ticker:
        return jsonify({"error": "missing ticker"}), 400

    url = generate_spotlight(ticker, horizon, user_id=None, email_opt_in=False)
    return jsonify({"url": url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    