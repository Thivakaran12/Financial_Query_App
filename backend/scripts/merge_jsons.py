#!/usr/bin/env python3
"""
Repair, merge and export LLM‐extracted JSON into a single payload for the dashboard.

1) Reads per‐PDF JSONs from data/interim/<slug>/json/
2) Fixes parse errors by extracting fenced JSON or re‐evaluating arithmetic
3) Coerces any remaining string expressions into floats
4) Writes merged array to frontend/financial-dashboard/public/data/<slug>/all.json
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Configuration ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT     = PROJECT_ROOT / "data" / "interim"
DST_ROOT     = PROJECT_ROOT / "frontend" / "financial-dashboard" / "public" / "data"

COMPANY_SLUGS: Dict[str, str] = {
    "Dipped Products":   "dipped-products",
    "Richard Pieris":    "richard-pieris",
}

# regex to pull out ```json { … } ``` snippets
JSON_SNIPPET = re.compile(r"```json\s*\n(\{.*?\})\s*```", re.DOTALL)

LOG_DIR = PROJECT_ROOT / "logs"


# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """
    Configure root logger to write to console and a file under logs/.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logfile = LOG_DIR / "merge_jsons.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger(__name__)


# ─── Utilities ────────────────────────────────────────────────────────────────
def eval_expr(expr: str) -> Optional[float]:
    """
    Safely evaluate a simple arithmetic expression and return its float value.
    Returns None if expression is invalid.
    """
    if not re.fullmatch(r"[\d\.\-\+\s\(\)]+", expr):
        return None
    try:
        return float(eval(expr, {}, {}))  # no builtins
    except Exception:
        return None


def repair_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    If record has 'parse_error' plus a 'raw_output', attempt to recover by:
      • parsing raw JSON directly, or
      • extracting a fenced ```json block```
    Remove error fields once fixed.
    """
    raw = rec.get("raw_output")
    if raw and rec.get("parse_error"):
        full_rec: Optional[Dict[str, Any]] = None

        # Try direct JSON parse
        try:
            if raw.strip().startswith("{"):
                full_rec = json.loads(raw)
                logger.info("Direct JSON parse succeeded")
        except Exception:
            full_rec = None

        # Try fenced-snippet
        if full_rec is None:
            m = JSON_SNIPPET.search(raw)
            if m:
                try:
                    full_rec = json.loads(m.group(1))
                    logger.info("Extracted fenced JSON snippet")
                except Exception:
                    full_rec = None

        # Merge fields if recovered
        if full_rec:
            for key in (
                "company", "symbol", "fiscal_year",
                "quarter", "period_end_date", "currency",
                "unit_multiplier", "revenue", "cogs",
                "gross_profit", "operating_expenses",
                "operating_income", "net_income",
            ):
                if key in full_rec:
                    rec[key] = full_rec[key]

        # Clean up
        rec.pop("raw_output", None)
        rec.pop("parse_error", None)

    # Evaluate any remaining string expressions
    for field in (
        "revenue", "cogs", "gross_profit",
        "operating_expenses", "operating_income", "net_income",
    ):
        val = rec.get(field)
        if isinstance(val, str):
            num = eval_expr(val)
            if num is not None:
                rec[field] = num

    return rec


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    """
    Iterate over each slug's interim JSON folder, merge and repair records,
    then write out consolidated all.json under the frontend data folder.
    """
    setup_logging()
    logger.info("Starting merge_jsons")

    for company_name, slug in COMPANY_SLUGS.items():
        # Look under data/interim/<slug>/json
        src_dir = SRC_ROOT / slug / "json"
        if not src_dir.exists():
            logger.warning("Source folder not found, skipping: %s", src_dir)
            continue

        # Load all JSON files
        records: List[Dict[str, Any]] = []
        for json_file in sorted(src_dir.glob("*.json")):
            try:
                rec = json.loads(json_file.read_text(encoding="utf-8"))
                records.append(rec)
            except Exception as exc:
                logger.error("Failed to read %s: %s", json_file, exc)

        # Repair and clean
        cleaned: List[Dict[str, Any]] = [repair_record(rec) for rec in records]

        # Write out
        out_dir = DST_ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "all.json"

        try:
            out_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
            logger.info("Wrote %d records → %s", len(cleaned), out_path.relative_to(DST_ROOT))
        except Exception as exc:
            logger.exception("Failed to write merged JSON for %s: %s", slug, exc)


if __name__ == "__main__":
    main()
