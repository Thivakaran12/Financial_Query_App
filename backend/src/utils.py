"""
utils.py

Shared helper functions for quarterly‐P&L extraction:
 - extract_qtr_snippet: snip out the “03 months to …” table
 - load_previous_qtr:  load the prior quarter’s JSON for diffing
 - post_validate:      detect YTD→QTR mismatches and auto‐fix
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

def extract_qtr_snippet(full_text: str) -> Tuple[str, str]:
    """
    Find the “03 months to …” header line in `full_text` and return:
      - snippet: all lines from the header up until the next blank line
      - header_text: the first line (the exact column heading)
    If not found, return (full_text, "").
    """
    lines = full_text.splitlines()
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith("03 months to")), None)
    if idx is None:
        return full_text, ""

    snippet_lines = []
    for line in lines[idx:]:
        if not line.strip():
            break
        snippet_lines.append(line)
    header_text = snippet_lines[0].strip()
    return "\n".join(snippet_lines), header_text

def load_previous_qtr(pdf_path: Path) -> Optional[Dict[str, Any]]:
    """
    Given a Path to a current-quarter file (PDF or JSON), look in the
    same 'json' directory for the previous JSON by sort order.
    Return its parsed dict, or None if none found.
    """
    # if user passed in the JSON itself, its parent is already the JSON folder
    if pdf_path.suffix.lower() == ".json":
        json_dir = pdf_path.parent
    else:
        # assume PDFs live alongside a 'json/' subfolder
        json_dir = pdf_path.parent / "json"

    if not json_dir.exists():
        return None

    siblings = sorted(json_dir.glob("*.json"))
    stems = [s.stem for s in siblings]
    try:
        idx = stems.index(pdf_path.stem)
    except ValueError:
        return None
    if idx == 0:
        return None

    prev_file = siblings[idx - 1]
    return json.loads(prev_file.read_text(encoding="utf-8"))

def post_validate(
    rec: Dict[str, Any],
    pdf_path: Path,
    max_qtr_rev: float = 50_000_000,
) -> None:
    """
    If revenue > `max_qtr_rev`, assume LLM pulled a YTD number.
    Subtract the prior quarter (loaded via load_previous_qtr) from
    each P&L field to recover the single-quarter figure, then set
    rec["ytd_qtr_fixed"]=True.
    """
    rev = rec.get("revenue", 0)
    if not isinstance(rev, (int, float)) or rev <= max_qtr_rev:
        return

    prev = load_previous_qtr(pdf_path)
    if not prev:
        return

    for fld in (
        "revenue",
        "cogs",
        "gross_profit",
        "operating_expenses",
        "operating_income",
        "net_income",
    ):
        curr_val = rec.get(fld)
        prev_val = prev.get(fld)
        if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
            rec[fld] = curr_val - prev_val

    rec["ytd_qtr_fixed"] = True
