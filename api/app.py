from fastapi import FastAPI
from mangum import Mangum
from api.spotlight import router as spotlight_router

app = FastAPI(title="DLENS API", version="1.0")

@app.get("/")
async def root():
    return {"status": "ok", "message": "DLENS API running 🚀"}

app.include_router(spotlight_router)

asgi_app = Mangum(app)   # for Vercel
