#!/usr/bin/env python3
"""
extract_interim_financials.py

Extract & structure quarterly P&L tables from raw CSE PDFs via an LLM.

Snip only the “03 months to …” table
Inject its exact header into the Jinja2 prompt
Post-validate & auto-fix YTD→QTR mismatches
Output per-PDF JSON and append to a per-company CSV
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pdfplumber
from dotenv import load_dotenv
from jinja2 import Template
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI

# ─── Shared utilities ─────────────────────────────────────────────────────────
from backend.src.utils import extract_qtr_snippet, post_validate

# ─── Constants & Paths ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
PROMPT_FILE = PROJECT_ROOT / "backend" / "src" / "prompts" / "financial_extraction.j2"
LOG_DIR = PROJECT_ROOT / "logs"

LLM_TIMEOUT = 60         # seconds per LLM call

COMPANY_MAP: Dict[str, str] = {
    "DIPD.N0000": "dipped-products",
    "REXP.N0000": "richard-pieris",
}

# ensure output dirs exist
for slug in COMPANY_MAP.values():
    for sub in ("json", "csv", "txt"):
        (INTERIM_DIR / slug / sub).mkdir(parents=True, exist_ok=True)

# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """Configure root logger to write to console and file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "extract_interim_financials.log", encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        handlers=handlers,
    )

logger = logging.getLogger(__name__)

# ─── LLM Client ──────────────────────────────────────────────────────────────
def llm_client() -> Any:
    """
    Initialize ChatOpenAI or AzureChatOpenAI using OPENAI_EMBEDDING_KEY.
    """
    embed_key = os.getenv("OPENAI_EMBEDDING_KEY") or os.getenv("openai_embedding_key")
    if not embed_key:
        logger.error("Missing OPENAI_EMBEDDING_KEY in environment")
        raise RuntimeError("Missing OPENAI_EMBEDDING_KEY")

    common = {"temperature": 0}
    if os.getenv("OPENAI_API_BASE"):
        client = AzureChatOpenAI(
            azure_endpoint=os.getenv("OPENAI_API_BASE"),
            azure_api_key=embed_key,
            azure_deployment=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_api_version=os.getenv("OPENAI_API_VERSION", "2024-02-01"),
            **common,
        )
    else:
        client = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_api_key=embed_key,
            **common,
        )

    logger.info("Initialized LLM client: %s", client.__class__.__name__)
    return client

# ─── Prompt Loader ───────────────────────────────────────────────────────────
def read_prompt() -> Template:
    """Read and return the Jinja2 prompt template."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    return Template(text)

# ─── PDF Snipping ────────────────────────────────────────────────────────────
def find_pnl_pages(pdf_path: Path) -> str:
    """Extract raw text from up to the first few pages for P&L detection."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:8]
        return "\n".join(p.extract_text() or "" for p in pages)

# ─── LLM Extraction ──────────────────────────────────────────────────────────
def ask_llm(
    tmpl: Template,
    header_text: str,
    snippet: str,
    example: Dict[str, Any],
    client: Any,
    pdf_name: str,
) -> Dict[str, Any]:
    """
    Send Jinja2-rendered prompt to LLM, parse JSON response,
    fallback to safe eval if JSON loads fails.
    """
    prompt = tmpl.render(
        header_text=header_text,
        content=snippet,
        example_output_format=json.dumps(example, indent=2),
    )
    resp = getattr(client, "invoke", client)(
        [HumanMessage(content=prompt)], timeout=LLM_TIMEOUT
    )
    raw = getattr(resp, "content", str(resp)).strip()

    # extract {...}
    start, end = raw.find("{"), raw.rfind("}")
    body = raw[start : end + 1] if start != -1 and end != -1 else raw

    try:
        return json.loads(body)
    except Exception:
        safe = body.replace("null", "None")
        try:
            rec = eval(safe, {"__builtins__": None}, {})
            if isinstance(rec, dict):
                return rec
        except Exception:
            pass

    logger.error("Bad JSON from LLM for %s: %s", pdf_name, raw)
    return {"parse_error": "bad_json", "raw": raw}

# ─── Output Writers ──────────────────────────────────────────────────────────
def write_outputs(rec: Dict[str, Any], pdf_path: Path) -> None:
    """
    Determine company slug, write JSON file, and append a CSV row.
    """
    slug = COMPANY_MAP.get(rec.get("symbol", ""), pdf_path.parent.name)

    # JSON
    out_json = INTERIM_DIR / slug / "json" / f"{pdf_path.stem}.json"
    out_json.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    logger.info("Wrote JSON → %s", out_json.relative_to(PROJECT_ROOT))

    # CSV
    out_csv = INTERIM_DIR / slug / "csv" / "pnl.csv"
    columns = [
        "company", "symbol", "fiscal_year", "quarter", "period_end_date",
        "currency", "unit_multiplier", "revenue", "cogs", "gross_profit",
        "operating_expenses", "operating_income", "net_income", "ytd_qtr_fixed",
    ]
    row = {col: rec.get(col, "") for col in columns}
    pd.DataFrame([row]).to_csv(
        out_csv, mode="a", header=not out_csv.exists(), index=False, columns=columns
    )
    logger.info("Appended CSV → %s", out_csv.relative_to(PROJECT_ROOT))

# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    """Orchestrate the full extraction pipeline over all raw PDFs."""
    setup_logging()
    load_dotenv()
    logger.info("Starting interim financial extraction")

    example_schema = {
        "company": "<COMPANY NAME>",
        "symbol": "<TICKER>",
        "fiscal_year": "YYYY/YY",
        "quarter": "Q1",
        "period_end_date": "YYYY-MM-DD",
        "currency": "LKR",
        "unit_multiplier": 1000,
        "revenue": 0,
        "cogs": 0,
        "gross_profit": 0,
        "operating_expenses": 0,
        "operating_income": 0,
        "net_income": 0,
    }

    client = llm_client()
    tmpl = read_prompt()

    total = succeeded = 0
    for pdf_path in RAW_DIR.rglob("*.pdf"):
        total += 1
        logger.info("Processing %s", pdf_path.relative_to(PROJECT_ROOT))

        full_text = find_pnl_pages(pdf_path)
        snippet, header = extract_qtr_snippet(full_text)

        # dump raw snippet
        txt_out = INTERIM_DIR / pdf_path.parent.name / "txt" / f"{pdf_path.stem}.txt"
        txt_out.write_text(snippet, encoding="utf-8")

        rec = ask_llm(tmpl, header, snippet, example_schema, client, pdf_path.name)
        if rec.get("parse_error"):
            logger.error("Skipping %s due to parse_error", pdf_path.name)
            continue

        post_validate(rec, pdf_path)
        write_outputs(rec, pdf_path)
        succeeded += 1

    logger.info("Done: %d/%d PDFs extracted", succeeded, total)


if __name__ == "__main__":
    main()
