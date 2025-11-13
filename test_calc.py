# tests/test_calc.py
from api.services.validator_v12 import validate_dlens_spotlight_v12

def test_validator_example_sample():
    # Load one of your gold samples to ensure the validator passes
    with open("api/resources/DLENS_Spotlight_TSLA_ID_251009_v12_Gold_v7.html", "r", encoding="utf-8") as f:
        html = f.read()
    ok, errors = validate_dlens_spotlight_v12(html)
    # If the old sample lacks some new checks (e.g., strict headers), adjust sample or relax during migration.
    assert ok, f"Sample failed validator: {errors}"
