from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_file
from pathlib import Path
from spotlight import generate_spotlight

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_REPORTS = BASE_DIR / "static_reports"

print("📌 Running from:", BASE_DIR)
print("📌 Reports folder:", STATIC_REPORTS)


@app.get("/")
def home():
    return send_file(BASE_DIR / "resources" / "index.html")


@app.post("/api/spotlight")
def api_spotlight():
    """Main endpoint — generates a Spotlight report."""
    data = request.get_json()

    print("\n==============================")
    print("🔥 RAW REQUEST BODY →", request.data)
    print("🔥 request.get_json() →", data)
    print("==============================\n")

    ticker = data.get("ticker", "").strip()
    years = int(data.get("projection_years", 10))

    if not ticker:
        return jsonify({"error": "ticker_missing"}), 400

    # Generate the report
    url = generate_spotlight(
        ticker=ticker,
        projection_years=years,
        user_id=data.get("user_id", "demo"),
        email_opt_in=data.get("email_opt_in", False)
    )

    print("RETURNING URL →", url)

    return jsonify({"url": url})



@app.get("/api/reports/<filename>")
def serve_report(filename):
    file_path = STATIC_REPORTS / filename
    if not file_path.exists():
        return "<h1>Report Not Found</h1>", 404

    return send_file(file_path)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

