from .llm_client import get_client

def gpt_generate_html(prompt, ticker, years):
    client = get_client()
    msg = f"Generate DLENS Spotlight for {ticker} over {years} years.\n\n{prompt}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output DLENS Spotlight HTML only."},
            {"role": "user", "content": msg}
        ]
    )

    return response.choices[0].message.content
