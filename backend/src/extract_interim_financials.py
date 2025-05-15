# #!/usr/bin/env python3
# """
# Slim-line extractor: CSE interim PDFs → JSON + CSV (via LLM)
# -----------------------------------------------------------
# * Walks Data/Raw/**/{pdf} (two companies)
# * Sends only the Consolidated P&L pages (or full document if not found)
#   to an LLM via Jinja2 prompt → structured JSON
# * Writes
#     Data/Interim/<Company>/json/<pdf-stem>.json
#     Data/Interim/<Company>/csv/pnl.csv   (appends)
# * Uses timeouts, logging, sanity checks, and a fallback mechanism.
# """
# from __future__ import annotations
# import json
# import logging
# import os
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# import pandas as pd
# import pdfplumber
# from dotenv import load_dotenv
# from jinja2 import Template
# from langchain.schema import HumanMessage
# from langchain_openai import ChatOpenAI, AzureChatOpenAI

# # ─────────── env & logging ───────────
# load_dotenv()
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)-8s %(message)s",
# )

# # ─────────── paths & config ──────────
# ROOT        = Path(__file__).resolve().parent.parent
# RAW_DIR     = ROOT / "Data" / "Raw"
# INTERIM_DIR = ROOT / "Data" / "Interim"
# PROMPT_FILE = ROOT / "src" / "prompts" / "financial_extraction.j2"
# MAX_PAGES   = 8      # pages to scan initially for P&L
# LLM_TIMEOUT = 60     # seconds per LLM call

# COMPANY_MAP: Dict[str, str] = {
#     "DIPD.N0000": "Dipped Products",
#     "REXP.N0000": "Richard Pieris",
# }

# # ensure output directories exist
# for comp in COMPANY_MAP.values():
#     (INTERIM_DIR / comp / "json").mkdir(parents=True, exist_ok=True)
#     (INTERIM_DIR / comp / "csv").mkdir(parents=True, exist_ok=True)

# # ─────────── helpers ─────────────────

# def llm_client() -> Any:
#     common = {"temperature": 0}
#     if os.getenv("OPENAI_API_BASE"):
#         client = AzureChatOpenAI(
#             azure_endpoint     = os.getenv("OPENAI_API_BASE"),
#             openai_api_version = os.getenv("OPENAI_API_VERSION", "2024-02-01"),
#             azure_deployment   = os.getenv("OPENAI_MODEL",       "gpt-4o"),
#             **common,
#         )
#     else:
#         client = ChatOpenAI(
#             model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
#             **common,
#         )
#     logging.info("LLM client initialized (%s)", client.__class__.__name__)
#     return client


# def read_prompt() -> Template:
#     if not PROMPT_FILE.exists():
#         raise FileNotFoundError(f"Prompt missing: {PROMPT_FILE}")
#     return Template(PROMPT_FILE.read_text(encoding="utf-8"))


# def find_pnl_pages(path: Path) -> List[str]:
#     """
#     Locate Group/Consolidated Income Statement pages.
#     Fallback to full document if none found in first MAX_PAGES.
#     """
#     with pdfplumber.open(path) as pdf:
#         pages = pdf.pages[:MAX_PAGES]
#         matched: List[str] = []
#         for pg in pages:
#             txt = pg.extract_text() or ""
#             if any(phrase in txt for phrase in (
#                 "Consolidated Income Statement",
#                 "STATEMENT OF PROFIT OR LOSS",
#                 "Group" and "Profit or Loss",
#             )):
#                 matched.append(txt)
#         if matched:
#             logging.info("Found %d P&L page(s) in %s", len(matched), path.name)
#             return matched
#         logging.warning(
#             "P&L heading not found in first %d pages of %s; using full document",
#             MAX_PAGES, path.name
#         )
#         return [pg.extract_text() or "" for pg in pdf.pages]


# def pdf_text(path: Path) -> str:
#     pages = find_pnl_pages(path)
#     return "\n".join(pages)


# def ask_llm(
#     tmpl: Template,
#     content: str,
#     example: Dict[str, Any],
#     client: Any,
#     pdf_name: str,
# ) -> Optional[Dict[str, Any]]:
#     prompt = tmpl.render(
#         content=content,
#         example_output_format=json.dumps(example, indent=2),
#     )
#     logging.info("Sending prompt to LLM for %s", pdf_name)
#     try:
#         resp = getattr(client, "invoke", client)(
#             [HumanMessage(content=prompt)],
#             timeout=LLM_TIMEOUT,
#         )
#     except Exception as e:
#         logging.error("LLM call failed for %s: %s", pdf_name, e)
#         return None
#     raw = getattr(resp, "content", str(resp)).strip()
#     logging.info("Received LLM response for %s", pdf_name)
#     try:
#         start, end = raw.find("{"), raw.rfind("}")
#         body = raw[start : end + 1] if start != -1 and end != -1 else raw
#         return json.loads(body)
#     except Exception:
#         logging.error("Failed to parse JSON for %s; raw output:\n%s", pdf_name, raw)
#         return None


# def company_from_path(pdf_path: Path) -> str:
#     """
#     Derive the company name from the parent directory under Data/Raw.
#     """
#     try:
#         return pdf_path.parent.name.strip()
#     except Exception:
#         return ""


# def write_outputs(rec: Dict[str, Any], pdf_path: Path) -> None:
#     # what model returned
#     llm_symbol  = str(rec.get("symbol") or "").strip()
#     llm_company = str(rec.get("company") or "").strip()
#     # what folder name indicates
#     path_company = company_from_path(pdf_path)

#     # choose folder: symbol → mapping, else folder name, else raw LLM company, else Unknown
#     company = (
#         COMPANY_MAP.get(llm_symbol)
#         or path_company
#         or llm_company
#         or "Unknown"
#     )

#     base_json = INTERIM_DIR / company / "json"
#     base_csv  = INTERIM_DIR / company / "csv"
#     base_json.mkdir(parents=True, exist_ok=True)
#     base_csv.mkdir(parents=True, exist_ok=True)

#     # write JSON
#     json_path = base_json / f"{pdf_path.stem}.json"
#     json_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
#     logging.info("JSON saved → %s", json_path.relative_to(ROOT))

#     # append CSV
#     csv_path = base_csv / "pnl.csv"
#     pd.DataFrame([rec]).to_csv(
#         csv_path,
#         mode="a",
#         header=not csv_path.exists(),
#         index=False
#     )
#     logging.info("Row appended → %s", csv_path.relative_to(ROOT))


# def main():
#     client = llm_client()
#     tmpl   = read_prompt()

#     # neutral example to avoid bias
#     example = {
#         "company":            "<COMPANY NAME>",
#         "symbol":             "<TICKER>",
#         "fiscal_year":        "YYYY/YY",
#         "quarter":            "Q1",
#         "period_end_date":    "YYYY-MM-DD",
#         "currency":           "LKR",
#         "unit_multiplier":    1000,
#         "revenue":            0,
#         "cogs":               0,
#         "gross_profit":       0,
#         "operating_expenses": 0,
#         "operating_income":   0,
#         "net_income":         0,
#     }

#     for pdf_path in RAW_DIR.rglob("*.pdf"):
#         logging.info("--- Processing %s ---", pdf_path.relative_to(ROOT))
#         text   = pdf_text(pdf_path)
#         record = ask_llm(tmpl, text, example, client, pdf_path.name)
#         if not record:
#             logging.warning("Skipping %s due to LLM errors", pdf_path.name)
#             continue

#         # Gross Profit sanity check
#         rev  = record.get("revenue", 0)
#         cogs = record.get("cogs", 0)
#         gp   = record.get("gross_profit", 0)
#         if abs(rev - cogs - gp) > 1:
#             logging.warning(
#                 "Inconsistency in Gross Profit for %s: rev %.0f – cogs %.0f != gp %.0f",
#                 pdf_path.name, rev, cogs, gp
#             )

#         # completeness check
#         required = [
#             "revenue", "cogs", "gross_profit",
#             "operating_expenses", "operating_income", "net_income",
#         ]
#         missing = [k for k in required if record.get(k) is None]
#         if missing:
#             logging.error(
#                 "Missing fields %s in %s — inspect folder for corrections",
#                 missing, pdf_path.name
#             )
#             continue

#         write_outputs(record, pdf_path)

#     logging.info("All PDFs processed. Outputs in Data/Interim/<Company>/…")


# if __name__ == "__main__":
#     main()




# #!/usr/bin/env python3
# """
# Slim-line extractor: CSE interim PDFs → JSON + CSV (via LLM)
# -----------------------------------------------------------
# * Walks backend/Data/Raw/**/{pdf}  (two companies)
# * Sends only the Consolidated P&L pages (or full document if not found)
#   to an LLM via Jinja2 prompt → structured JSON
# * Writes
#     backend/Data/Interim/<Company>/json/<pdf-stem>.json
#     backend/Data/Interim/<Company>/csv/pnl.csv   (appends)
# * Uses timeouts, logging, sanity checks, and a fallback mechanism.
# """
# from __future__ import annotations
# import json
# import logging
# import os
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# import pandas as pd
# import pdfplumber
# from dotenv import load_dotenv
# from jinja2 import Template
# from langchain.schema import HumanMessage
# from langchain_openai import ChatOpenAI, AzureChatOpenAI

# # ─────────── env & logging ───────────
# load_dotenv()
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)-8s %(message)s",
# )

# # ─────────── paths & config ──────────
# # script is at backend/src/extract_interim_financials.py, so parent.parent == backend
# ROOT        = Path(__file__).resolve().parent.parent
# RAW_DIR     = ROOT / "Data" / "Raw"
# INTERIM_DIR = ROOT / "Data" / "Interim"
# PROMPT_FILE = ROOT / "src" / "prompts" / "financial_extraction.j2"
# MAX_PAGES   = 8      # pages to scan initially for P&L
# LLM_TIMEOUT = 60     # seconds per LLM call

# COMPANY_MAP: Dict[str, str] = {
#     "DIPD.N0000": "Dipped Products",
#     "REXP.N0000": "Richard Pieris",
# }

# # ensure output directories exist
# for comp in COMPANY_MAP.values():
#     (INTERIM_DIR / comp / "json").mkdir(parents=True, exist_ok=True)
#     (INTERIM_DIR / comp / "csv").mkdir(parents=True, exist_ok=True)

# # ─────────── helpers ─────────────────

# def llm_client() -> Any:
#     common = {"temperature": 0}
#     if os.getenv("OPENAI_API_BASE"):  # Azure
#         client = AzureChatOpenAI(
#             azure_endpoint     = os.getenv("OPENAI_API_BASE"),
#             openai_api_version = os.getenv("OPENAI_API_VERSION", "2024-02-01"),
#             azure_deployment   = os.getenv("OPENAI_MODEL", "gpt-4o"),
#             **common,
#         )
#     else:
#         client = ChatOpenAI(
#             model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
#             **common,
#         )
#     logging.info("LLM client initialized (%s)", client.__class__.__name__)
#     return client


# def read_prompt() -> Template:
#     if not PROMPT_FILE.exists():
#         raise FileNotFoundError(f"Prompt missing: {PROMPT_FILE}")
#     return Template(PROMPT_FILE.read_text(encoding="utf-8"))


# def find_pnl_pages(path: Path) -> List[str]:
#     """
#     Locate Group/Consolidated Income Statement pages.
#     Fallback to full document if none found in first MAX_PAGES.
#     """
#     with pdfplumber.open(path) as pdf:
#         heads = pdf.pages[:MAX_PAGES]
#         matched: List[str] = []
#         for pg in heads:
#             txt = pg.extract_text() or ""
#             if any(
#                 phrase in txt
#                 for phrase in (
#                     "Consolidated Income Statement",
#                     "STATEMENT OF PROFIT OR LOSS",
#                     "Group Profit or Loss",
#                 )
#             ):
#                 matched.append(txt)
#         if matched:
#             logging.info("Found %d P&L page(s) in %s", len(matched), path.name)
#             return matched

#         # fallback to full doc
#         logging.warning(
#             "P&L heading not found in first %d pages of %s; using full document",
#             MAX_PAGES, path.name
#         )
#         return [pg.extract_text() or "" for pg in pdf.pages]


# def pdf_text(path: Path) -> str:
#     pages = find_pnl_pages(path)
#     return "\n".join(pages)


# def ask_llm(
#     tmpl: Template,
#     content: str,
#     example: Dict[str, Any],
#     client: Any,
#     pdf_path: Path,
# ) -> Dict[str, Any]:
#     """
#     Returns a dict in all cases. On JSON-parse failures it returns
#     a minimal record with raw_output so we still write out a JSON.
#     """
#     prompt = tmpl.render(
#         content=content,
#         example_output_format=json.dumps(example, indent=2),
#     )
#     logging.info("Sending prompt to LLM for %s", pdf_path.name)
#     try:
#         resp = getattr(client, "invoke", client)(
#             [HumanMessage(content=prompt)],
#             timeout=LLM_TIMEOUT,
#         )
#     except Exception as e:
#         logging.error("LLM call failed for %s: %s", pdf_path.name, e)
#         # still return something so we write a JSON
#         return {
#             "company": pdf_path.parent.name,
#             "symbol": "",
#             "error": f"LLM call failed: {e}"
#         }

#     raw = getattr(resp, "content", str(resp)).strip()
#     logging.info("Received LLM response for %s", pdf_path.name)

#     try:
#         start, end = raw.find("{"), raw.rfind("}")
#         body = raw[start:end+1] if start != -1 and end != -1 else raw
#         return json.loads(body)
#     except Exception as e:
#         logging.error("Failed to parse JSON for %s: %s", pdf_path.name, e)
#         # fallback record preserves raw
#         return {
#             "company": pdf_path.parent.name,
#             "symbol": "",
#             "raw_output": raw,
#             "parse_error": str(e),
#         }


# def company_from_path(pdf_path: Path) -> str:
#     """
#     Derive the company folder-name from the parent dir under Data/Raw.
#     """
#     return pdf_path.parent.name.strip()


# def write_outputs(rec: Dict[str, Any], pdf_path: Path) -> None:
#     llm_symbol  = str(rec.get("symbol") or "").strip()
#     llm_company = str(rec.get("company") or "").strip()
#     path_company = company_from_path(pdf_path)

#     # choose the folder: first by exact symbol match, else by raw folder-name,
#     # else by whatever LLM said, else "Unknown"
#     company = (
#         COMPANY_MAP.get(llm_symbol)
#         or path_company
#         or llm_company
#         or "Unknown"
#     )

#     base_json = INTERIM_DIR / company / "json"
#     base_csv  = INTERIM_DIR / company / "csv"
#     base_json.mkdir(parents=True, exist_ok=True)
#     base_csv.mkdir(parents=True, exist_ok=True)

#     # JSON
#     json_path = base_json / f"{pdf_path.stem}.json"
#     json_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
#     logging.info("JSON saved → %s", json_path.relative_to(ROOT))

#     # CSV
#     csv_path = base_csv / "pnl.csv"
#     pd.DataFrame([rec]).to_csv(
#         csv_path,
#         mode="a",
#         header=not csv_path.exists(),
#         index=False
#     )
#     logging.info("Row appended → %s", csv_path.relative_to(ROOT))


# def main():
#     client = llm_client()
#     tmpl   = read_prompt()

#     example = {
#         "company":            "<COMPANY NAME>",
#         "symbol":             "<TICKER>",
#         "fiscal_year":        "YYYY/YY",
#         "quarter":            "Q1",
#         "period_end_date":    "YYYY-MM-DD",
#         "currency":           "LKR",
#         "unit_multiplier":    1000,
#         "revenue":            0,
#         "cogs":               0,
#         "gross_profit":       0,
#         "operating_expenses": 0,
#         "operating_income":   0,
#         "net_income":         0,
#     }

#     count = 0
#     total = 0

#     # pick up ANY .pdf or .PDF in Raw/**
#     for pdf_path in RAW_DIR.rglob("*"):
#         if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
#             continue
#         total += 1
#         logging.info("--- Processing %s ---", pdf_path.relative_to(ROOT))

#         text   = pdf_text(pdf_path)
#         record = ask_llm(tmpl, text, example, client, pdf_path)

#         # sanity‐check Gross Profit
#         try:
#             rev  = float(record.get("revenue", 0))
#             cogs = float(record.get("cogs", 0))
#             gp   = float(record.get("gross_profit", 0))
#             if abs(rev - cogs - gp) > 1:
#                 logging.warning(
#                     "Inconsistency in Gross Profit for %s: rev %.0f – cogs %.0f != gp %.0f",
#                     pdf_path.name, rev, cogs, gp
#                 )
#         except Exception:
#             pass  # skip if non-numeric

#         # write JSON + CSV for every file
#         write_outputs(record, pdf_path)
#         count += 1

#     logging.info("Done: wrote %d/%d PDFs → JSON+CSV under Data/Interim", count, total)


# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
"""
Slim-line extractor: CSE interim PDFs → JSON + CSV (via LLM) + raw text dumps
---------------------------------------------------------------------------
* Walks backend/Data/Raw/**/{pdf}  (two companies)
* Extracts only the Consolidated P&L pages (or full document if not found)
  and saves that text to backend/Data/Interim/<Company>/txt/*.txt
* Sends that same text to an LLM via Jinja2 prompt → structured JSON
* Writes
    backend/Data/Interim/<Company>/json/<pdf-stem>.json
    backend/Data/Interim/<Company>/csv/pnl.csv   (appends)
* Uses timeouts, logging, sanity checks, and a fallback mechanism.
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
# script lives in backend/src/, so parent.parent == backend
ROOT        = Path(__file__).resolve().parent.parent
RAW_DIR     = ROOT / "Data" / "Raw"
INTERIM_DIR = ROOT / "Data" / "Interim"
PROMPT_FILE = ROOT / "src" / "prompts" / "financial_extraction.j2"
MAX_PAGES   = 8      # pages to scan initially for P&L
LLM_TIMEOUT = 60     # seconds per LLM call

COMPANY_MAP: Dict[str, str] = {
    "DIPD.N0000": "Dipped Products",
    "REXP.N0000": "Richard Pieris",
}

# ensure output directories exist
for comp in COMPANY_MAP.values():
    (INTERIM_DIR / comp / "json").mkdir(parents=True, exist_ok=True)
    (INTERIM_DIR / comp / "csv").mkdir(parents=True, exist_ok=True)
    # also prepare a 'txt' folder for raw P&L text
    (INTERIM_DIR / comp / "txt").mkdir(parents=True, exist_ok=True)

# ─────────── helpers ─────────────────

def llm_client() -> Any:
    common = {"temperature": 0}
    if os.getenv("OPENAI_API_BASE"):  # Azure
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

def find_pnl_pages(path: Path) -> List[str]:
    """
    Locate Group/Consolidated Income Statement pages.
    Fallback to full document if none found in first MAX_PAGES.
    """
    with pdfplumber.open(path) as pdf:
        heads = pdf.pages[:MAX_PAGES]
        matched: List[str] = []
        for pg in heads:
            txt = pg.extract_text() or ""
            if any(phrase in txt for phrase in (
                "Consolidated Income Statement",
                "STATEMENT OF PROFIT OR LOSS",
                "Group Profit or Loss",
            )):
                matched.append(txt)
        if matched:
            logging.info("Found %d P&L page(s) in %s", len(matched), path.name)
            return matched

        # fallback to full doc
        logging.warning(
            "P&L heading not found in first %d pages of %s; using full document",
            MAX_PAGES, path.name
        )
        return [pg.extract_text() or "" for pg in pdf.pages]

def pdf_text(path: Path) -> str:
    pages = find_pnl_pages(path)
    return "\n".join(pages)

def ask_llm(
    tmpl: Template,
    content: str,
    example: Dict[str, Any],
    client: Any,
    pdf_path: Path,
) -> Dict[str, Any]:
    prompt = tmpl.render(
        content=content,
        example_output_format=json.dumps(example, indent=2),
    )
    logging.info("Sending prompt to LLM for %s", pdf_path.name)
    try:
        resp = getattr(client, "invoke", client)(
            [HumanMessage(content=prompt)],
            timeout=LLM_TIMEOUT,
        )
    except Exception as e:
        logging.error("LLM call failed for %s: %s", pdf_path.name, e)
        return {
            "company": pdf_path.parent.name,
            "symbol": "",
            "error": f"LLM call failed: {e}"
        }

    raw = getattr(resp, "content", str(resp)).strip()
    logging.info("Received LLM response for %s", pdf_path.name)

    try:
        start, end = raw.find("{"), raw.rfind("}")
        body = raw[start : end+1] if start != -1 and end != -1 else raw
        return json.loads(body)
    except Exception as e:
        logging.error("Failed to parse JSON for %s: %s", pdf_path.name, e)
        return {
            "company": pdf_path.parent.name,
            "symbol": "",
            "raw_output": raw,
            "parse_error": str(e),
        }

def company_from_path(pdf_path: Path) -> str:
    """ Derive the interim folder name from the Raw subfolder """
    return pdf_path.parent.name.strip()

def write_outputs(rec: Dict[str, Any], pdf_path: Path) -> None:
    llm_symbol  = str(rec.get("symbol") or "").strip()
    llm_company = str(rec.get("company") or "").strip()
    path_company = company_from_path(pdf_path)

    # pick final company folder
    company = (
        COMPANY_MAP.get(llm_symbol)
        or path_company
        or llm_company
        or "Unknown"
    )

    # JSON & CSV dirs already exist
    base_json = INTERIM_DIR / company / "json"
    base_csv  = INTERIM_DIR / company / "csv"

    # write JSON
    json_path = base_json / f"{pdf_path.stem}.json"
    json_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    logging.info("JSON saved → %s", json_path.relative_to(ROOT))

    # append CSV
    csv_path = base_csv / "pnl.csv"
    pd.DataFrame([rec]).to_csv(
        csv_path,
        mode="a",
        header=not csv_path.exists(),
        index=False
    )
    logging.info("Row appended → %s", csv_path.relative_to(ROOT))

def main():
    client = llm_client()
    tmpl   = read_prompt()

    example = {
        "company":            "<COMPANY NAME>",
        "symbol":             "<TICKER>",
        "fiscal_year":        "YYYY/YY",
        "quarter":            "Q1",
        "period_end_date":    "YYYY-MM-DD",
        "currency":           "LKR",
        "unit_multiplier":    1000,
        "revenue":            0,
        "cogs":               0,
        "gross_profit":       0,
        "operating_expenses": 0,
        "operating_income":   0,
        "net_income":         0,
    }

    count = 0
    total = 0

    for pdf_path in RAW_DIR.rglob("*.pdf"):
        total += 1
        logging.info("--- Processing %s ---", pdf_path.relative_to(ROOT))

        # 1) extract just the P&L text
        text = pdf_text(pdf_path)

        # 2) save raw text to INTERIM/.../txt
        folder = company_from_path(pdf_path)
        txt_dir = INTERIM_DIR / folder / "txt"
        txt_dir.mkdir(parents=True, exist_ok=True)
        (txt_dir / f"{pdf_path.stem}.txt").write_text(text, encoding="utf-8")
        logging.info("Raw text saved → %s", (txt_dir / f"{pdf_path.stem}.txt").relative_to(ROOT))

        # 3) ask the LLM to parse those numbers
        record = ask_llm(tmpl, text, example, client, pdf_path)

        # 4) sanity‐check
        try:
            rev  = float(record.get("revenue", 0))
            cogs = float(record.get("cogs", 0))
            gp   = float(record.get("gross_profit", 0))
            if abs(rev - cogs - gp) > 1:
                logging.warning(
                    "Inconsistency in GP for %s: rev %.0f – cogs %.0f != gp %.0f",
                    pdf_path.name, rev, cogs, gp
                )
        except Exception:
            pass

        # 5) write JSON+CSV
        write_outputs(record, pdf_path)
        count += 1

    logging.info("Done: wrote %d/%d PDFs → JSON+CSV+TXT under Data/Interim", count, total)

if __name__ == "__main__":
    main()
