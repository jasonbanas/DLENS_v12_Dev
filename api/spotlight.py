import json

# Import generator in a way that works both locally and on Vercel
try:
    from services.generator import gpt_generate_html
except ModuleNotFoundError:
    from api.services.generator import gpt_generate_html


# -------------------------------
# Vercel Serverless Function
# -------------------------------
def handler(request):
    try:
        # Parse incoming JSON
        body = request.json()

        ticker = body.get("ticker", "UNKNOWN")
        years = int(body.get("years", 5))

        # CORRECT WAY to call generator (keyword-only)
        html = gpt_generate_html(
            prompt="Spotlight generation",
            ticker=ticker,
            years=years
        )

        filename = f"DLENS_Spotlight_{ticker}_LocalMock.html"

        # Build JSON response for Vercel
        response = {
            "attempts": [{"ok": True, "meta": {"ticker": ticker}}],
            "meta": {"ticker": ticker},
            "url": f"/reports/demo/{filename}",
            "vercel_mode": True,
            "html_preview": html[:200] + "..."
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except Exception as e:
        error_response = {
            "error": "server_error",
            "detail": str(e),
            "message": "Internal Server Error"
        }

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_response)
        }
