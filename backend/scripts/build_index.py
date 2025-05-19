#!/usr/bin/env python3
"""
Build or update the Chroma vector store for the LLM chatbot.

This script:
  * Reads P&L text files from data/interim/<company>/txt/
  * Loads corresponding JSON metadata from data/interim/<company>/json/
  * Splits text into ~2,000-character chunks (~500 tokens)
  * Embeds using OpenAI text-embedding-ada-002
  * Persists to data/index/ via Chroma
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ─── Monkey-patch NumPy 2.0 dtype removals ────────────────────────────────────
np.float_ = np.float64  # type: ignore
np.int_ = np.int64      # type: ignore
np.uint = np.uint64     # type: ignore

# ─── Constants ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR     = PROJECT_ROOT / "data"
INTERIM_DIR  = DATA_DIR / "interim"
INDEX_DIR    = DATA_DIR / "index"
LOG_DIR      = PROJECT_ROOT / "logs"
ENV_FILE     = PROJECT_ROOT / ".env"

CHUNK_SIZE    = 2_000
CHUNK_OVERLAP =   200

# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """
    Configure root logger to write INFO+ to both stdout (UTF-8 safe) and a file.
    """
    LOG_DIR.mkdir(exist_ok=True)
    logfile = LOG_DIR / "build_index.log"

    # File handler (UTF-8)
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))

    # Console handler: wrap stdout in UTF-8 with replace on error
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ch = logging.StreamHandler(utf8_stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))

    # Clear existing handlers and install ours
    logging.root.handlers.clear()
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(fh)
    logging.root.addHandler(ch)


# ─── Environment & API Key ────────────────────────────────────────────────────
def load_api_key() -> str:
    """
    Load the OpenAI embedding key from .env, stripping any Azure vars.
    """
    load_dotenv(ENV_FILE)
    for azure_var in (
        "OPENAI_API_BASE",
        "OPENAI_API_VERSION",
        "OPENAI_API_TYPE",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
    ):
        os.environ.pop(azure_var, None)

    key = os.getenv("OPENAI_EMBEDDING_KEY") or os.getenv("openai_embedding_key")
    if not key:
        logging.error("Missing OPENAI_EMBEDDING_KEY in environment; aborting.")
        sys.exit(1)
    return key


# ─── Main Indexing Logic ─────────────────────────────────────────────────────
def build_index() -> None:
    """
    Read interim P&L text + metadata, chunk, embed, and persist a Chroma vector store.
    """
    setup_logging()
    api_key = load_api_key()
    logging.info("Embedding key loaded; initializing embedder.")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    embedder = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=api_key,
    )
    logging.info("OpenAIEmbeddings ready (model=text-embedding-ada-002)")

    docs = []
    txt_paths = list(INTERIM_DIR.rglob("txt/*.txt"))
    logging.info("Discovered %d interim TXT files in %s", len(txt_paths), INTERIM_DIR)

    for txt_path in txt_paths:
        stem = txt_path.stem
        company = txt_path.parent.parent.name
        json_path = txt_path.parent.parent / "json" / f"{stem}.json"
        if not json_path.exists():
            logging.warning("Skipping %s (no JSON metadata)", txt_path.relative_to(INTERIM_DIR))
            continue

        raw_meta = json.loads(json_path.read_text(encoding="utf-8"))
        meta = {
            k: v
            for k, v in {
                **raw_meta,
                "company_slug": company.lower().replace(" ", "-"),
                "source_txt": txt_path.name,
            }.items()
            if isinstance(v, (str, int, float, bool))
        }

        text = txt_path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        logging.info("  - %s -> %d chunks", txt_path.relative_to(INTERIM_DIR), len(chunks))

        for chunk in chunks:
            docs.append(Document(page_content=chunk, metadata=meta))

    if not docs:
        logging.error("No document chunks found; nothing to index.")
        sys.exit(1)

    t0 = perf_counter()
    try:
        vectordb = Chroma.from_documents(
            docs,
            embedding=embedder,
            persist_directory=str(INDEX_DIR),
        )
        elapsed = perf_counter() - t0
        logging.info(
            "Successfully indexed %d chunks -> %s (%.1fs)",
            len(docs),
            INDEX_DIR.relative_to(PROJECT_ROOT),
            elapsed,
        )
    except Exception:
        logging.exception("Chroma index build failed")
        sys.exit(1)


if __name__ == "__main__":
    build_index()
