
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .market_feed import MarketFeed
from .rules_engine import RulesEngine

class CalcCoreV12:
    def __init__(self):
        self.feed = MarketFeed()
        self.rules = RulesEngine()

    def _timestamp(self, as_of_utc: Optional[str]) -> str:
        if as_of_utc:
            return as_of_utc
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def build_hunt(self, tickers: List[str], as_of_utc: Optional[str], include_kb: bool, kb):
        rows = []
        ts = self._timestamp(as_of_utc)
        for t in tickers:
            csp, sources = self.feed.get_two_source_csp(t)
            metrics = self.feed.get_baseline_metrics_v12(t)
            # Apply KB-derived adjustments via rules
            cards = kb.search(entity=t, since_days=180) if include_kb else []
            metrics = self.rules.apply_cards(metrics, cards)
            rows.append({
                "ticker": t,
                "company": self.feed.get_company_name(t),
                "csp": csp,
                "sources": sources,
                "ts": ts,
                **metrics,
                "kb_cards": cards
            })
        # Sort by DUU desc, then DDI
        rows.sort(key=lambda r: (-r["DUU"], -r.get("DDI", 0)))
        return {"as_of": ts, "rows": rows}

    def build_spotlight(self, ticker: str, as_of_utc: Optional[str], include_kb: bool, kb):
        ts = self._timestamp(as_of_utc)
        csp, sources = self.feed.get_two_source_csp(ticker)
        metrics = self.feed.get_baseline_metrics_v12(ticker)
        cards = kb.search(entity=ticker, since_days=180) if include_kb else []
        metrics = self.rules.apply_cards(metrics, cards)
        return {
            "as_of": ts,
            "ticker": ticker,
            "company": self.feed.get_company_name(ticker),
            "csp": csp,
            "sources": sources,
            **metrics,
            "kb_cards": cards
        }
