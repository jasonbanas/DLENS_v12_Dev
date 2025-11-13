import os
from typing import List, Dict
import openai

def complete(messages: List[Dict[str, str]], model: str | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    openai.api_key = api_key

    base_url = os.getenv("OPENAI_BASE_URL")  # optional
    if base_url:
        openai.base_url = base_url

    model = model or os.getenv("LLM_MODEL", "gpt-5")
    resp = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=20000,          # generous so full HTML fits
        timeout=120,               # seconds; avoid hanging on big prompts
    )
    return resp.choices[0].message.content
