# api/routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/api/spotlight")
async def spotlight(request: Request):
    data = await request.json()
    ticker = data.get("ticker")
    years = data.get("years")
    document = data.get("document")

    # Placeholder logic – replace with your real validator later
    if not document or "DLENS Disruptor Spotlight" not in document:
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_failed",
                "details": ["Missing or incorrect DLENS document structure."]
            },
        )

    return {"ok": True, "ticker": ticker, "years": years}
