# backend/scripts/merge_jsons.py

import json
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
# ────────────────────────────────────────────────────────────────────────────

def main():
    DST_ROOT.mkdir(parents=True, exist_ok=True)

    for company_name, slug in COMPANIES.items():
        src_dir = SRC_ROOT / company_name / "json"
        if not src_dir.exists():
            print(f"Warning: source folder not found: {src_dir}")
            continue

        # load & merge
        merged = []
        for fn in sorted(src_dir.glob("*.json")):
            with fn.open(encoding="utf-8") as f:
                merged.append(json.load(f))

        # write out
        out_dir = DST_ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "all.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)

        print(f"Wrote {len(merged)} records → {out_file.relative_to(DST_ROOT)}")

if __name__ == "__main__":
    main()
