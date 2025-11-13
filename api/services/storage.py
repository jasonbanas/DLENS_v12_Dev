from pathlib import Path
import time

ROOT = Path("static/reports")

def save_report(user_id: str, ticker: str, html: str):
    ts = time.strftime("%y%m%d", time.gmtime())
    fname = f"DLENS_Spotlight_{ticker}_ID_{ts}_GoldStandard_v12.html"
    folder = ROOT / user_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / fname
    path.write_text(html, encoding="utf-8")
    url = f"/static/reports/{user_id}/{fname}"
    return path, url
