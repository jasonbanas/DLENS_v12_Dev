# api/app.py
from flask import Flask, request, jsonify, send_from_directory, send_file
from pathlib import Path
import os, re

TITLE_REQUIRED = "DLENS Disruptor Spotlight"

# ---------- PATHS ----------
API_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = API_DIR / "resources"
REPORTS_DIR = API_DIR / "reports"
SERVICES_DIR = API_DIR / "services"

REPORTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

# ---------- HEALTH ----------
@app.get("/api/ping")
def ping():
    return {"ok": True}

# ---------- SANITIZE ----------
def sanitize_ticker(v: str):
    if not v:
        raise ValueError("Missing ticker")
    v = v.strip().upper()
    if not re.fullmatch(r"[A-Z0-9\-]{1,12}", v):
        raise ValueError("Invalid ticker")
    return v

def clamp_years(n):
    try:
        n = int(n)
    except:
        n = 10
    return max(1, min(20, n))

# ---------- GENERATOR (STUB) ----------
def generate_dlens_report(ticker, years):
    return f"""
    <html>
    <head><title>{TITLE_REQUIRED} — {ticker}</title></head>
    <body>
      <h1>DLENS Disruptor Spotlight — {ticker}</h1>

      <h2>Disruption Lens</h2>
      DUU Score: 8.7/10 → DUU (Most-Likely Price, {years}y): $320.00 (= 1.5× CSP $213.33 ≈ 50%) • Probability: 72%

      <h2>What is the company</h2>
      {ticker} designs, manufactures, and sells advanced technology solutions.

      <h2>Why now</h2>
      Strong market momentum makes the next decade ideal for {ticker}'s expansion.

      <h2>Feasibility</h2>
      Score 9/10 — conditions support large scale-up.

      <h2>Founder Execution Premium</h2>
      Premium 8/10 — leadership strong and proven.

      <h2>Peer Comparison</h2>
      <table border="1">
        <tr><th>Company</th><th>Tech</th><th>Scale</th><th>Subsidy</th><th>Position</th></tr>
        <tr><td>{ticker}</td><td>Integrated Platform</td><td>High</td><td>Low</td><td>Leader</td></tr>
        <tr><td>BYD</td><td>Battery</td><td>High</td><td>Medium</td><td>Strong</td></tr>
      </table>

      <h2>Truth Audit</h2>
      Independent verification passes DLENS Gold Standard.

      <h2>Metrics to Watch</h2>
      Revenue growth • Operating margin • Cash flow stability

      <h2>Milestones</h2>
      Product launch • Expansion milestone • R&D breakthrough

      <h2>Risks</h2>
      Regulation • Market volatility • Execution bottlenecks

      <h2>What would change</h2>
      Disruption or geopolitical shifts may impact valuation.

      <h2>Decision-Ready Conclusion</h2>
      {ticker} passes DLENS v12 Gold Standard.

      <h2>CSP (2-source)</h2>
      Yahoo Finance: $213.33<br>
      Bloomberg: $213.30<br>
      Timestamp: UTC 2025-11-10 12:00
    </body>
    </html>
    """

# ---------- MAIN ENDPOINT ----------
@app.post("/api/spotlight")
def spotlight():
    try:
        payload = request.get_json(force=True)
        print("DEBUG PAYLOAD:", payload)

        ticker = sanitize_ticker(payload.get("ticker"))
        years = clamp_years(payload.get("years"))

    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    html = generate_dlens_report(ticker, years)

    REPORTS_DIR.mkdir(exist_ok=True)
    fname = f"DLENS_{ticker}.html"
    fpath = REPORTS_DIR / fname
    fpath.write_text(html, encoding="utf-8")

    return jsonify({"url": f"/reports/{fname}"}), 201

# ---------- SERVE REPORT ----------
@app.get("/reports/<filename>")
def serve_report(filename):
    f = REPORTS_DIR / filename
    if not f.exists():
        return "Not found", 404
    return send_file(f, mimetype="text/html")

# ---------- SERVE UI ----------
@app.get("/")
def home():
    return send_from_directory(str(RESOURCES_DIR), "index.html")
