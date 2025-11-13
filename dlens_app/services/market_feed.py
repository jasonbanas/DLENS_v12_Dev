from datetime import datetime

def get_two_source_csp(ticker: str):
    # demo stub: two public sources + timestamps
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    price_a = 250.12
    price_b = 251.05
    composed = round((price_a + price_b) / 2, 2)
    return {
        "anchors": [
            {"source": "Yahoo Finance", "price": price_a, "as_of": now},
            {"source": "Google Finance", "price": price_b, "as_of": now},
        ],
        "composed": composed,
        "composed_as_of": now,
    }
