from flask import Flask, render_template, request, jsonify
from spotlight import generate_spotlight
import os

app = Flask(__name__, template_folder="templates")

@app.route("/")
def home():
    return render_template("spotlight.html")

@app.route("/spotlight")
def spotlight_page():
    return render_template("spotlight.html")

@app.route("/api/spotlight", methods=["POST"])
def api_spotlight():
    try:
        ticker = request.form.get("ticker")
        horizon = request.form.get("horizon", "3")
        user_id = "render_user"
        email_opt_in = False

        file_url = generate_spotlight(ticker, horizon, user_id, email_opt_in)
        return jsonify({"success": True, "url": file_url})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# STATIC REPORT FILE SERVER
@app.route("/api/reports/<path:filename>")
def serve_report(filename):
    return app.send_static_file(f"reports/{filename}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
