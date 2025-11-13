import json

# Import generator
try:
    from services.generator import gpt_generate_html
except ModuleNotFoundError:
    from api.services.generator import gpt_generate_html


def handler(request):
    """
    Vercel Python Serverless Function Entry Point
    """

    try:
        # Vercel provides request.body in bytes
        body_bytes = request.body
        body = json.loads(body_bytes.decode("utf-8"))

        ticker = body.get("ticker", "UNKNOWN")
        years = int(body.get("years", 5))

        html = gpt_generate_html(
            prompt="Spotlight generation",
            ticker=ticker,
            years=years
        )

        filename = f"DLENS_Spotlight_{ticker}_Preview.html"

        response = {
            "ok": True,
            "ticker": ticker,
            "years": years,
            "url": f"/reports/{filename}",
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
