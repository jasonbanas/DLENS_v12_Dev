from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# Import generator
try:
    from api.services.generator import gpt_generate_html
except ModuleNotFoundError:
    from services.generator import gpt_generate_html

router = APIRouter(prefix="/api")

@router.post("/spotlight")
async def spotlight(request: Request):
    data = await request.json()

    ticker = data.get("ticker", "UNKNOWN")
    years = int(data.get("years", 5))

    html = gpt_generate_html(
        prompt="Spotlight generation",
        ticker=ticker,
        years=years
    )

    return JSONResponse({
        "ok": True,
        "ticker": ticker,
        "years": years,
        "html_preview": html[:200] + "..."
    })
