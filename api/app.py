from flask import Flask, request, jsonify
from spotlight import generate_spotlight   # your generator logic

app = Flask(__name__)

@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({"ok": True})

@app.route("/api/spotlight", methods=["POST"])
def spotlight():
    # Validate JSON
    if not request.is_json:
        return jsonify({
            "error": "bad_request",
            "details": ["Request must include JSON body"]
        }), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "error": "bad_request",
            "details": ["Invalid JSON format"]
        }), 400

    # Extract fields
    query = data.get("query")
    years = data.get("years")
    user_id = data.get("user_id")
    email_opt_in = data.get("email_opt_in", False)

    # Required fields
    missing = []
    if not query: missing.append("query")
    if not years: missing.append("years")
    if missing:
        return jsonify({
            "error": "bad_request",
            "details": [f"Missing fields: {', '.join(missing)}"]
        }), 400

    # --- RUN YOUR GENERATOR ---
    try:
        result_url = generate_spotlight(
            ticker=query.upper(),
            projection_years=int(years),
            user_id=user_id,
            email_opt_in=email_opt_in
        )

        return jsonify({
            "ok": True,
            "url": result_url
        })

    except Exception as e:
        return jsonify({
            "error": "internal_error",
            "details": [str(e)]
        }), 500


# Required for Vercel
def handler(request, *args):
    return app(request, *args)
