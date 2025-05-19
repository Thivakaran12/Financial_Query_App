import json
from pathlib import Path
import tempfile

import pytest
from backend.src.utils import post_validate

def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")

def test_post_validate_subtracts_previous(tmp_path):
    # Create a fake folder structure:
    # tmp_path/company/json/q1.json, q2.json
    company_dir = tmp_path / "company"
    json_dir = company_dir / "json"
    json_dir.mkdir(parents=True)

    # previous quarter (q1)
    prev = {
        "revenue": 1000,
        "cogs": 400,
        "gross_profit": 600,
        "operating_expenses": 200,
        "operating_income": 400,
        "net_income": 300,
    }
    write_json(json_dir / "q1.json", prev)

    # current quarter (q2) but erroneously YTD
    curr = {
        "revenue": 150000000,
        "cogs": -60000000,
        "gross_profit": 90000000,
        "operating_expenses": -30000000,
        "operating_income": 60000000,
        "net_income": 40000000,
    }
    write_json(json_dir / "q2.json", curr)

    # load rec and run post_validate with a low threshold
    rec = curr.copy()
    pdf_path = json_dir / "q2.json"
    post_validate(rec, pdf_path, max_qtr_rev=1_000_000)

    # each field should be curr - prev
    assert rec["revenue"] == 150000000 - 1000
    assert rec["cogs"] == -60000000 - 400
    assert rec["gross_profit"] == 90000000 - 600
    assert rec["operating_expenses"] == -30000000 - 200
    assert rec["operating_income"] == 60000000 - 400
    assert rec["net_income"] == 40000000 - 300
    assert rec.get("ytd_qtr_fixed") is True

def test_post_validate_no_previous(tmp_path):
    # only one file => nothing to subtract
    company_dir = tmp_path / "company"
    json_dir = company_dir / "json"
    json_dir.mkdir(parents=True)

    curr = {"revenue": 2000000}
    write_json(json_dir / "only.json", curr)

    rec = curr.copy()
    pdf_path = json_dir / "only.json"
    post_validate(rec, pdf_path, max_qtr_rev=1_000_000)

    # revenue is unchanged and no flag set
    assert rec["revenue"] == 2000000
    assert "ytd_qtr_fixed" not in rec
