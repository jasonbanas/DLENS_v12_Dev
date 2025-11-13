from flask import Blueprint, request, jsonify
from pathlib import Path
import re

bp = Blueprint("reports", __name__)

BASE = Path("static/reports")
NAME_RE = re.compile(r"^DLENS_Spotlight_[A-Z0-9\-]+_ID_\d{6}_GoldStandard_v12\.html$")

@bp.get("/api/reports")
def list_reports():
    user_id = request.args.get("user_id") or request.args.get("user")  # accept either param
    if not user_id or not user_id.isalnum():
        return jsonify({"error": "bad_request", "detail": "invalid user_id"}), 400

    folder = BASE / user_id
    folder.mkdir(parents=True, exist_ok=True)

    items = []
    for p in folder.glob("*.html"):
        if not NAME_RE.fullmatch(p.name):
            continue
        st = p.stat()
        items.append({
            "filename": p.name,
            "created_at": int(st.st_mtime),
            "size_bytes": st.st_size,
            "public_url": f"/static/reports/{user_id}/{p.name}",
        })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify(items)
