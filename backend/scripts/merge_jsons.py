# backend/scripts/merge_jsons.py

import json
import re
from pathlib import Path

# ─── CONFIGURATION ─────────────────────────────────────────────────────────
# Where your extractor dropped the per‐PDF JSONs:
SRC_ROOT = Path(__file__).resolve().parent.parent / "Data" / "Interim"

# Project root is two levels up from this script (backend/scripts → backend → project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Where your CRA app will serve static data from:
DST_ROOT = PROJECT_ROOT / "frontend" / "financial-dashboard" / "public" / "data"

# Map the exact folder-names under `Data/Interim` to URL-friendly slugs:
COMPANIES = {
    "Dipped Products":   "dipped-products",
    "Richard Pieris":    "richard-pieris",
}

# Regex to extract JSON object from raw_output fenced by ```json
JSON_SNIPPET = re.compile(r"```json\s*\n(\{.*?\})\s*```", re.DOTALL)

# ────────────────────────────────────────────────────────────────────────────
def eval_expr(expr: str) -> float | None:
    """
    Safely evaluate simple arithmetic expressions like:
      -726.944 - 1526.344
      11566.520 - (-1820.842 + -5981.170)
    """
    if not re.fullmatch(r"[\d\.\-\+\s\(\)]+", expr):
        return None
    try:
        return float(eval(expr, {}, {}))
    except:
        return None
# ────────────────────────────────────────────────────────────────────────────

def eval_expr(expr: str) -> float | None:
    """
    Safely evaluate simple arithmetic expressions like
    -1820.842 + -5981.170  or  11566.520 - (-1820.842 + -5981.170)
    """
    # Only allow digits, decimal points, parentheses, spaces and +/-
    if not re.fullmatch(r"[\d\.\-\+\s\(\)]+", expr):
        return None
    try:
        return float(eval(expr, {}, {}))
    except Exception:
        return None

# ────────────────────────────────────────────────────────────────────────────

# def main():
#     DST_ROOT.mkdir(parents=True, exist_ok=True)

#     for company_name, slug in COMPANIES.items():
#         src_dir = SRC_ROOT / company_name / "json"
#         if not src_dir.exists():
#             print(f"Warning: source folder not found: {src_dir}")
#             continue

#         # load & merge
#         merged = []
#         for fn in sorted(src_dir.glob("*.json")):
#             with fn.open(encoding="utf-8") as f:
#                 merged.append(json.load(f))

#         cleaned = []
#         numeric_fields = [
#             "revenue", "cogs", "gross_profit",
#             "operating_expenses", "operating_income", "net_income"
#         ]
#         for rec in merged:
#             if "parse_error" in rec:
#                 # try to repair each numeric field
#                 for fld in numeric_fields:
#                     val = rec.get(fld)
#                     if isinstance(val, str):
#                         repaired = eval_expr(val)
#                         if repaired is not None:
#                             rec[fld] = repaired
#                 # if we've removed the string issues, drop the error markers
#                 rec.pop("raw_output", None)
#                 rec.pop("parse_error", None)
#             cleaned.append(rec)

#         # write out
#         out_dir = DST_ROOT / slug
#         out_dir.mkdir(parents=True, exist_ok=True)
#         out_file = out_dir / "all.json"
#         with out_file.open("w", encoding="utf-8") as f:
#             json.dump(merged, f, indent=2)

#         print(f"Wrote {len(merged)} records → {out_file.relative_to(DST_ROOT)}")

# def main():
#     DST_ROOT.mkdir(parents=True, exist_ok=True)

#     for company_name, slug in COMPANIES.items():
#         src_dir = SRC_ROOT / company_name / "json"
#         if not src_dir.exists():
#             print(f"Warning: source folder not found: {src_dir}")
#             continue

#         # 1) load all JSONs
#         merged = []
#         for fn in sorted(src_dir.glob("*.json")):
#             with fn.open(encoding="utf-8") as f:
#                 merged.append(json.load(f))

#         # 2) repair and merge data
#         cleaned = []
#         for rec in merged:
#             # if raw_output exists, extract full JSON and merge fields
#             raw = rec.get("raw_output")
#             if raw and "parse_error" in rec:
#                 m = JSON_SNIPPET.search(raw)
#                 if m:
#                     try:
#                         full = json.loads(m.group(1))
#                         # override rec with full JSON values
#                         rec.update({k: full[k] for k in full if k in (
#                             "company","symbol","fiscal_year","quarter",
#                             "period_end_date","currency","unit_multiplier",
#                             "revenue","cogs","gross_profit",
#                             "operating_expenses","operating_income","net_income"
#                         )})
#                     except Exception:
#                         pass
#                 # drop raw_output and parse_error keys
#                 rec.pop("raw_output", None)
#                 rec.pop("parse_error", None)
#             # now ensure numeric fields are floats
#             for fld in ("revenue","cogs","gross_profit",
#                         "operating_expenses","operating_income","net_income"):
#                 val = rec.get(fld)
#                 if isinstance(val, str):
#                     repaired = eval_expr(val)
#                     if repaired is not None:
#                         rec[fld] = repaired
#             cleaned.append(rec)

#         # 3) write out repaired data
#         out_dir = DST_ROOT / slug
#         out_dir.mkdir(parents=True, exist_ok=True)
#         out_file = out_dir / "all.json"
#         with out_file.open("w", encoding="utf-8") as f:
#             json.dump(cleaned, f, indent=2)

#         print(f"Wrote {len(cleaned)} records → {out_file.relative_to(DST_ROOT)}")


def main():
    DST_ROOT.mkdir(parents=True, exist_ok=True)

    for company_name, slug in COMPANIES.items():
        src_dir = SRC_ROOT / company_name / "json"
        if not src_dir.exists():
            print(f"Warning: source folder not found: {src_dir}")
            continue

        # 1) Load all JSON records
        merged = []
        for fn in sorted(src_dir.glob("*.json")):
            with fn.open(encoding="utf-8") as f:
                merged.append(json.load(f))

        # 2) Repair broken entries and cleanup
        cleaned = []
        for rec in merged:
            raw = rec.get("raw_output")
            if raw and rec.get("parse_error"):
                full_rec = None
                # Attempt to parse raw as plain JSON
                try:
                    if raw.strip().startswith('{'):
                        full_rec = json.loads(raw)
                except:
                    full_rec = None
                # Fallback: extract fenced JSON
                if not full_rec:
                    m = JSON_SNIPPET.search(raw)
                    if m:
                        try:
                            full_rec = json.loads(m.group(1))
                        except:
                            full_rec = None
                # Merge fields from the full_rec if obtained
                if full_rec:
                    for key in (
                        "company","symbol","fiscal_year","quarter",
                        "period_end_date","currency","unit_multiplier",
                        "revenue","cogs","gross_profit",
                        "operating_expenses","operating_income","net_income"
                    ):
                        if key in full_rec:
                            rec[key] = full_rec[key]
                # Remove error metadata
                rec.pop("raw_output", None)
                rec.pop("parse_error", None)

            # Evaluate any remaining string expressions into floats
            for field in (
                "revenue","cogs","gross_profit",
                "operating_expenses","operating_income","net_income"
            ):
                val = rec.get(field)
                if isinstance(val, str):
                    res = eval_expr(val)
                    if res is not None:
                        rec[field] = res

            cleaned.append(rec)

        # 3) Write out repaired & valid data
        out_dir = DST_ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "all.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)

        print(f"Wrote {len(cleaned)} records → {out_file.relative_to(DST_ROOT)}")
        
if __name__ == "__main__":
    main()
