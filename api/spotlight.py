import os
from openai import OpenAI

def handler(request):
    try:
        body = request.json()

        ticker = body.get("ticker", "").strip().upper()
        years = int(body.get("projection_years", 10))

        if not ticker:
            return {"error": "ticker_missing"}, 400

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        prompt = f"""
        Generate a detailed DLENS v12 style spotlight report for {ticker}.
        Include:
        - Company Summary
        - DUU Score
        - CSP Anchors
        - 10-year projection table
        - Highlights & Risks

        Output strictly in HTML with <section> tags.
        Use a dark theme (black, blue, neon green).
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        html_output = completion.choices[0].message.content

        safe_name = f"DLENS_Spotlight_{ticker}.html"
        out_path = f"static_reports/{safe_name}"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_output)

        return {
            "url": f"/api/reports/{safe_name}"
        }

    except Exception as e:
        return {"error": str(e)}, 500
