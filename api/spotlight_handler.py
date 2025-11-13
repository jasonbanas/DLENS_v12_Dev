import json

try:
    from api.services.generator import gpt_generate_html
except ModuleNotFoundError:
    from services.generator import gpt_generate_html


def handler(request):
    try:
        body = request.json()

        ticker = body.get("ticker", "UNKNOWN")
        years = int(body.get("years", 5))

        html = gpt_generate_html(
            prompt="Spotlight generation",
            ticker=ticker,
            years=years
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "ok": True,
                "ticker": ticker,
                "years": years,
                "html_preview": html[:200] + "..."
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "server_error",
                "detail": str(e)
            })
        }
