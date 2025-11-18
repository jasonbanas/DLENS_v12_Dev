from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from spotlight import generate_spotlight
from werkzeug.utils import safe_join

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_REPORTS = BASE_DIR / "static_reports"

print("📌 Running from:", BASE_DIR)
print("📌 Reports folder:", STATIC_REPORTS)


@app.get("/")
def home():
    return send_from_directory(BASE_DIR / "resources", "index.html")


@app.post("/api/spotlight")
def api_spotlight():

    data = request.get_json()

    print("\n==============================")
    print("🔥 RAW REQUEST BODY →", request.data)
    print("🔥 request.get_json() →", data)
    print("==============================\n")

    if not data:
        return jsonify({"error": "invalid_json"}), 400

    ticker = data.get("ticker", "").strip()
    years = int(data.get("projection_years", 10))

    if not ticker:
        return jsonify({"error": "ticker_missing"}), 400

    # Generate report
    url = generate_spotlight(
        ticker=ticker,
        projection_years=years,
        user_id=data.get("user_id", "demo"),
        email_opt_in=data.get("email_opt_in", False)
    )

    print("RETURNING URL →", url)

    return jsonify({"url": url})


# -----------------------------------------------------
# FIXED REPORT SERVING ROUTE (100% working)
# -----------------------------------------------------
@app.get("/api/reports/<path:filename>")
def serve_report(filename):

    safe_path = safe_join(STATIC_REPORTS, filename)
    file_path = Path(safe_path)

    print("📄 Requested file:", file_path)

    if not file_path.exists():
        print("❌ FILE NOT FOUND:", file_path)
        return "<h1>Report Not Found</h1>", 404

    print("✅ Serving File OK!")
    return send_from_directory(STATIC_REPORTS, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
