import json
from pathlib import Path
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
DATASET = BASE_DIR / "companies.json"

# Load all companies
with open(DATASET, "r", encoding="utf-8") as f:
    COMPANIES = json.load(f)

# If API key exists
client = None
try:
    client = OpenAI()
except Exception:
    client = None


def ai_score_company(keyword, company):
    """
    Uses OpenAI to generate:
    - DUU Score
    - 10-year ML price
    - Summary insight
    """

    if client is None:
        # fallback if no API key configured
        return {
            "duu": 7.5,
            "ml_price": 250,
            "summary": f"Relevance to '{keyword}' based on sector match."
        }

    prompt = f"""
    You are DLENS. Score this company for the keyword "{keyword}".

    Company: {company['name']}
    Sector: {company['sector']}

    Return JSON with:
    - duu (0-10)
    - ml_price (realistic 10-year)
    - summary (40-60 words)
    """

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(rsp.choices[0].message.content)

    except Exception:
        return {
            "duu": 7.2,
            "ml_price": 240,
            "summary": f"Static fallback relevance for '{keyword}'."
        }

def run_hunt(keyword, limit=10):

    keyword = keyword.lower().strip()

    results = []
    for c in COMPANIES:

        # simple matching rule
        if keyword in c["name"].lower() or keyword in c["sector"].lower():
            score = ai_score_company(keyword, c)

            results.append({
                "ticker": c["ticker"],
                "company": c["name"],
                "sector": c["sector"],
                "duu": score["duu"],
                "ml_price": score["ml_price"],
                "summary": score["summary"],
                "spotlight_url": f"/api/reports/DLENS_Spotlight_{c['ticker']}.html"
            })

    # Sort highest DUU first
    results = sorted(results, key=lambda x: x["duu"], reverse=True)

    return results[:limit]
