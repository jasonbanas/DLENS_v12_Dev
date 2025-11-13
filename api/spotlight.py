import json
from api.services.generator import gpt_generate_html

def handler(request):
    try:
        body = request.json()
        query = body.get("query")
        years = body.get("years", 5)

        html = gpt_generate_html(
            prompt="DLENS Spotlight",
            ticker=query,
            years=years
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "ok": True,
                "url": f"data:text/html;charset=utf-8,{html}"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
