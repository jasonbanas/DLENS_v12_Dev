from api.services.market_feed import get_two_source_csp
from api.rules_engine import build_prompt
from api.services.html_render import gpt_generate_html
import re
tkr, years = "TSLA", 10
html = gpt_generate_html(build_prompt(tkr, years, get_two_source_csp(tkr), None, None))
m = re.search(r"(DUU\s*Score:[^\n<]+)", html, flags=re.I)
print("HAS_DUU:", bool(m))
print("DUU:", m.group(1) if m else "NOT FOUND")
