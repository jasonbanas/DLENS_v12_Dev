import json

# Import your mock HTML generator
try:
    from api.services.generator import gpt_generate_html
except ModuleNotFoundError:
    from services.generator import gpt_generate_html


def handler(request):
    try:
        # Vercel passes request as a dict-like object
        body = request.json()

        ticker = body.get("ticker", "UNKNOWN")
        years = int(body.get("years", 5))

        html = gpt_generate_html(
            prompt="Spotlight generation",
            ticker=ticker,
            years=years
        )

        filename = f"DLENS_Spotlight_{ticker}_Mock.html"

        response = {
            "ok": True,
            "url": f"/reports/{filename}",
            "ticker": ticker,
            "years": years,
            "html_preview": html[:200] + "..."
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "internal_server_error",
                "detail": str(e)
            })
        }
