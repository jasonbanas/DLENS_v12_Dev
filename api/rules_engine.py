from pathlib import Path

def _read(p: str) -> str:
    return Path(p).read_text(encoding="utf-8")

# Make sure these two files exist (adjust paths if your layout differs)
RULES_HTML = _read("api/resources/DLENS_v12_Gold_Definitions_and_Rules_251012.html")
SPOTLIGHT_HTML = _read("api/resources/disruptor_spotlight.html")

NO_DRIFT_GUARD = (
    "Never add, rename, or reorder sections beyond what is defined in 'Gold Definitions'. "
    "Preserve exact headings, sequence, and required blocks."
)

SECTION_WHITELIST = ["Overview","Peer Table","Truth Audit","Compliance Checklist","CSP Sources","TradingView"]

PROMPT_TEMPLATE = f"""
You are the DLENS Disruptor Spotlight generator (v12 Gold).
Follow the **Gold Definitions** and **Spotlight scaffold** exactly.
{NO_DRIFT_GUARD}

<GoldDefinitions>
{RULES_HTML}
</GoldDefinitions>

<SpotlightScaffold>
{SPOTLIGHT_HTML}
</SpotlightScaffold>

Hard constraints:
- Only produce HTML matching the scaffold.
- Sections allowed: {SECTION_WHITELIST} — do not introduce new ones.
- Include TradingView script tag and new TradingView.widget(...).
- Include CSP two-source block (Google Finance + Yahoo Finance) with a UTC timestamp chip.
"""

def build_prompt(extra_hints: str | None = None) -> str:
    return PROMPT_TEMPLATE + ("\n<!-- Hints -->\n" + extra_hints if extra_hints else "")
