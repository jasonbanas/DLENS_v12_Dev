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

        response = {
            "ok": True,
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
            "body": json.dumps({"error": str(e)})
        }
