
import json, os, datetime
from typing import List

class KBClient:
    def __init__(self, path: str = None):
        self.path = path or os.environ.get("DLENS_KB_PATH", "/mnt/data/DLENS_v12_Dev_Package/kb/cards.jsonl")

    def search(self, entity: str, since_days: int = 180) -> List[dict]:
        results = []
        now = datetime.datetime.utcnow()
        since = now - datetime.timedelta(days=since_days)
        if not os.path.exists(self.path):
            return results
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    card = json.loads(line)
                    if entity.upper() in [e.upper() for e in card.get("entities", [])]:
                        rd = datetime.datetime.fromisoformat(card["source"]["recorded_date"])
                        if rd >= since:
                            results.append(card)
                except Exception:
                    continue
        return results[:10]
