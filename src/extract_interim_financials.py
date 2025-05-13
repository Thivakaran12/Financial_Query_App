#!/usr/bin/env python3
"""
Slim‑line extractor: CSE interim PDFs → JSON + CSV (via LLM)
-----------------------------------------------------------
* Walks Data/Raw/**/{pdf} (two companies)
* Sends first N pages to an LLM via Jinja2 prompt → structured JSON
* Writes
    Data/Interim/<Company>/json/<pdf‑stem>.json
    Data/Interim/<Company>/csv/pnl.csv   (appends)
* Uses timeouts and logging for reliability.
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pdfplumber
from dotenv import load_dotenv
from jinja2 import Template
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI

# ─────────── env & logging ───────────
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)

# ─────────── paths & config ──────────
ROOT        = Path(__file__).resolve().parent.parent
RAW_DIR     = ROOT / "Data" / "Raw"
INTERIM_DIR = ROOT / "Data" / "Interim"
PROMPT_FILE = ROOT / "src" /"prompts" / "financial_extraction.j2"
MAX_PAGES   = 8      # how many pages to send per PDF
LLM_TIMEOUT = 60     # seconds per LLM call

COMPANY_MAP: Dict[str, str] = {
    "DIPD.N0000": "Dipped Products",
    "REXP.N0000": "Richard Pieris",
}

# create output directories
for comp in COMPANY_MAP.values():
    (INTERIM_DIR / comp / "json").mkdir(parents=True, exist_ok=True)
    (INTERIM_DIR / comp / "csv").mkdir(parents=True, exist_ok=True)

# ─────────── helpers ─────────────────

def llm_client() -> Any:
    """Return ChatOpenAI or AzureChatOpenAI depending on env."""
    common = {"temperature": 0}
    if os.getenv("OPENAI_API_BASE"):
        client = AzureChatOpenAI(
            azure_endpoint     = os.getenv("OPENAI_API_BASE"),
            openai_api_version = os.getenv("OPENAI_API_VERSION", "2024-02-01"),
            azure_deployment   = os.getenv("OPENAI_MODEL", "gpt-4o"),
            **common,
        )
    else:
        client = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            **common,
        )
    logging.info("LLM client initialized (%s)", client.__class__.__name__)
    return client


def read_prompt() -> Template:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt missing: {PROMPT_FILE}")
    return Template(PROMPT_FILE.read_text(encoding="utf-8"))


def pdf_text(path: Path) -> str:
    logging.info("Reading up to %d pages from %s", MAX_PAGES, path.name)
    pages: List[str] = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages[:MAX_PAGES]:
            pages.append(pg.extract_text() or "")
    text = "\n".join(pages)
    logging.info("Extracted %d pages from %s", len(pages), path.name)
    return text


def ask_llm(
    tmpl: Template,
    content: str,
    example: Dict[str, Any],
    client: Any,
    pdf_name: str,
) -> Optional[Dict[str, Any]]:
    prompt = tmpl.render(
        content=content,
        example_output_format=json.dumps(example, indent=2),
    )
    logging.info("🚀 Sending prompt to LLM for %s", pdf_name)
    try:
        # use .invoke with timeout if supported
        resp = getattr(client, 'invoke', client)(
            [HumanMessage(content=prompt)],
            timeout=LLM_TIMEOUT,
        )
    except Exception as e:
        logging.error("⚠️ LLM call failed for %s: %s", pdf_name, e)
        return None
    raw = getattr(resp, 'content', str(resp)).strip()
    logging.info("✅ Received LLM response for %s", pdf_name)
    try:
        start, end = raw.find("{"), raw.rfind("}")
        body = raw[start:end+1] if start != -1 and end != -1 else raw
        data = json.loads(body)
        return data
    except Exception as e:
        logging.error("💥 Failed to parse JSON for %s; raw output:\n%s", pdf_name, raw)
        return None


def write_outputs(rec: Dict[str, Any], pdf_path: Path) -> None:
    symbol  = rec.get("symbol")
    company = COMPANY_MAP.get(symbol, rec.get("company", "Unknown")).strip()
    base    = INTERIM_DIR / company

    # JSON
    json_path = base / "json" / f"{pdf_path.stem}.json"
    json_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    logging.info("JSON saved → %s", json_path.relative_to(ROOT))

    # CSV
    csv_path = base / "csv" / "pnl.csv"
    df = pd.DataFrame([rec])
    df.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)
    logging.info("Row appended → %s", csv_path.relative_to(ROOT))

# ─────────── main ────────────────────

def main():
    client = llm_client()
    tmpl   = read_prompt()
    example = {
        "company": "Dipped Products PLC",
        "symbol": "DIPD.N0000",
        "fiscal_year": "2021/22",
        "quarter": "Q2",
        "period_end_date": "2021-09-30",
        "currency": "LKR",
        "unit_multiplier": 1000,
        "revenue": 0, "cogs": 0, "gross_profit": 0,
        "operating_expenses": 0, "operating_income": 0, "net_income": 0,
    }

    for pdf_path in RAW_DIR.rglob("*.pdf"):
        logging.info("--- Processing %s ---", pdf_path.relative_to(ROOT))
        text = pdf_text(pdf_path)
        record = ask_llm(tmpl, text, example, client, pdf_path.name)
        if record:
            write_outputs(record, pdf_path)
        else:
            logging.warning("Skipping %s due to previous errors", pdf_path.name)

    logging.info(" All PDFs processed. Outputs in Data/Interim/<Company>/…")

if __name__ == "__main__":
    main()
