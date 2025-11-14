# ---------- CREATE SPOTLIGHT (GET + POST SUPPORTED) ----------
@app.route("/api/spotlight", methods=["GET", "POST"])
def create_spotlight():
    user_id = _get_user_id()

    if RATE_ENABLED and not allow(user_id, "/api/spotlight"):
        return jsonify({"error": "rate_limited", "detail": "Too many requests"}), 429

    # ---------- INPUT HANDLING ----------
    try:
        if request.method == "GET":
            # Allow browser-friendly requests: /api/spotlight?ticker=AAPL
            ticker = sanitize_ticker(request.args.get("ticker", ""))
            years = clamp_years(request.args.get("years", 6))

        else:  # POST
            payload = request.get_json(force=True) or {}
            print("DEBUG PAYLOAD:", payload)

            ticker = sanitize_ticker(payload.get("ticker"))
            years = clamp_years(payload.get("years", 6))
            

    except Exception as e:
        return jsonify({"error": "bad_request", "detail": str(e)}), 400

    # ---------- DYNAMIC IMPORT (generator + validator) ----------
    try:
        base = Path(__file__).resolve().parent / "services"
        gen_path = base / "generator.py"
        val_path = base / "validator.py"

        spec_gen = importlib.util.spec_from_file_location("generator", gen_path)
        spec_val = importlib.util.spec_from_file_location("validator", val_path)

        generator = importlib.util.module_from_spec(spec_gen)
        validator = importlib.util.module_from_spec(spec_val)

        spec_gen.loader.exec_module(generator)
        spec_val.loader.exec_module(validator)

        gpt_generate_html = generator.gpt_generate_html
        validate_html = validator.validate

        app.logger.info("[DLENS] generator + validator dynamically loaded ✅")

    except Exception as e:
        app.logger.error(f"[DLENS] dynamic import failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "error": "server_misconfigured",
            "detail": "generator/validator not available"
        }), 500

    # ---------- GENERATE + VALIDATE ----------
    attempts, repair_hints = [], None

    for _ in range(MAX_ATTEMPTS):
        try:
            html = gpt_generate_html(build_prompt(repair_hints), ticker, years)
        except Exception as e:
            app.logger.error(f"[DLENS] generator runtime error: {e}")
            return jsonify({"error": "upstream_unreachable", "detail": str(e)}), 502

        html = _enforce_required_title(html)
        ok, errs, meta = validate_html(html)
        attempts.append({"ok": bool(ok), "errs": errs, "meta": meta})

        if ok:
            path, url = save_report(user_id, ticker, html)
            log_event("report_ok", user_id=user_id, ticker=ticker, years=years, path=str(path), meta=meta)

            # If GET request → redirect user to HTML
            if request.method == "GET":
                return send_file(path, mimetype="text/html")

            # POST → JSON API response
            return jsonify({"url": url, "meta": meta, "attempts": attempts}), 201

        repair_hints = f"Fix ONLY these issues: {errs}. Keep all passing sections verbatim."

    # ---------- FAIL ----------
    last_errs = attempts[-1]["errs"] if attempts else ["no_attempts"]
    log_event("report_fail", user_id=user_id, ticker=ticker, years=years, errs=last_errs)

    return jsonify({
        "error": "validation_failed",
        "details": last_errs,
        "attempts": attempts
    }), 422
