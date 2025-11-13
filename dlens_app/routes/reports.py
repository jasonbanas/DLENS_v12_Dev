# api/routes/reports.py
from flask import Blueprint, request, jsonify
from pathlib import Path
import os, time, httpx

bp = Blueprint("reports", __name__)
BACKEND = os.getenv("STORAGE_BACKEND", "local")

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_ROOT = BASE_DIR / "static" / "reports"

@bp.get("/api/reports")
def list_reports():
    user = request.args.get("user_id") or request.args.get("user") or "demo"

    items = []
    if BACKEND == "vercel_blob":
        token = os.environ["BLOB_READ_WRITE_TOKEN"]
        prefix = os.getenv("BLOB_BUCKET_PREFIX", "dlens/reports")
        base = f"{prefix}/{user}/"
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                "https://api.vercel.com/v2/blob",
                headers={"Authorization": f"Bearer {token}"},
                params={"prefix": base, "mode": "folded"}
            )
            r.raise_for_status()
            data = r.json()
            # returns {blobs:[{pathname,size,uploadedAt,url,...}]}
            for b in sorted(data.get("blobs", []), key=lambda x: x["uploadedAt"], reverse=True):
                items.append({
                    "filename": b["pathname"].split("/")[-1],
                    "created_at": int(b["uploadedAt"] / 1000),
                    "size_bytes": int(b.get("size", 0)),
                    "public_url": b["url"],
                })
    else:
        folder = LOCAL_ROOT / user
        folder.mkdir(parents=True, exist_ok=True)
        for p in sorted(folder.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True):
            items.append({
                "filename": p.name,
                "created_at": int(p.stat().st_mtime),
                "size_bytes": p.stat().st_size,
                "public_url": f"/static/reports/{user}/{p.name}",
            })

    return jsonify(items)
