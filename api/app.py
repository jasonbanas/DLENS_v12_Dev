import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# --- Safe Import: works both locally and on Vercel ---
try:
    from services.generator import gpt_generate_html
except ModuleNotFoundError:
    # fallback when Vercel doesn’t recognize package context
    from api.services.generator import gpt_generate_html

# --------------------------------------------------
# Initialize FastAPI
# --------------------------------------------------
app = FastAPI(title="DLENS Spotlight API", version="1.0")

# --------------------------------------------------
# Health check endpoint
# --------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "DLENS API running on Vercel 🚀"}

# --------------------------------------------------
# Main spotlight endpoint
# --------------------------------------------------
@app.post("/api/spotlight")
async def spotlight(request: Request):
    try:
        data = await request.json()
        ticker = data.get("ticker", "UNKNOWN")
        years = int(data.get("years", 5))

        html = gpt_generate_html("Spotlight generation", ticker, years)

        # Do NOT write to disk (Vercel file system is read-only)
        filename = f"DLENS_Spotlight_{ticker}_LocalMock.html"
        return JSONResponse({
            "attempts": [{"ok": True, "meta": {"ticker": ticker}}],
            "meta": {"ticker": ticker},
            "url": f"/reports/demo/{filename}",
            "vercel_mode": True,
            "html_preview": html[:200] + "..."
        })

    except Exception as e:
        return JSONResponse(
            {
                "error": "server_error",
                "detail": str(e),
                "message": "Internal Server Error (check generator or imports)"
            },
            status_code=500
        )

# --------------------------------------------------
# Local dev runner (ignored by Vercel)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Running DLENS API locally at http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
