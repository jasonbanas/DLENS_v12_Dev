from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services.generator import gpt_generate_html
import os

# --------------------------------------------------
# ✅ Initialize FastAPI
# --------------------------------------------------
app = FastAPI(title="DLENS Spotlight API", version="1.0")

# --------------------------------------------------
# ✅ Health check endpoint
# --------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "DLENS API is running on Vercel 🚀"}

# --------------------------------------------------
# ✅ Main spotlight endpoint
# --------------------------------------------------
@app.post("/api/spotlight")
async def spotlight(request: Request):
    try:
        # Parse JSON request
        data = await request.json()
        ticker = data.get("ticker", "UNKNOWN")
        years = int(data.get("years", 5))

        # Generate HTML (mock if LOCAL_MODE=True)
        html = gpt_generate_html("Spotlight generation", ticker, years)

        # ✅ We don't write to disk in Vercel — return path + mock HTML snippet
        filename = f"DLENS_Spotlight_{ticker}_LocalMock.html"
        return JSONResponse({
            "attempts": [{"ok": True, "meta": {"ticker": ticker}}],
            "meta": {"ticker": ticker},
            "url": f"/reports/demo/{filename}",
            "html_preview": html[:250] + "...",  # small preview for debugging
            "vercel_mode": True
        })

    except Exception as e:
        # Catch and display any internal errors
        return JSONResponse(
            {
                "error": "server_error",
                "detail": str(e),
                "message": "Internal Server Error (check generator or env vars)"
            },
            status_code=500
        )

# --------------------------------------------------
# ✅ Optional: local dev runner (ignored by Vercel)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Running DLENS API locally at http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
