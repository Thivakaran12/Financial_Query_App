#!/usr/bin/env python3
"""
Build / update the Chroma vector-store for the LLM chat-bot.

 • Reads every P&L text file under backend/Data/Interim/<Company>/txt/
 • Matches each one to its backend/Data/Interim/<Company>/json/ metadata
 • Splits into ~2 000-character chunks (≈500 tokens)
 • Embeds with text-embedding-ada-002 using your openai_embedding_key
 • Persists to backend/index/
"""
from __future__ import annotations
import os
import sys
import json
import logging
from time import perf_counter
from pathlib import Path

from dotenv import load_dotenv
from langchain.docstore.document      import Document
from langchain.text_splitter          import RecursiveCharacterTextSplitter
from langchain_openai                 import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ────────────────────────────────────────────────────────────────
# 1) ENV & LOGGING
# ────────────────────────────────────────────────────────────────
load_dotenv()  # loads backend/.env

# strip out any Azure-specific vars so the SDK never switches away from api.openai.com
for var in (
    "OPENAI_API_BASE", "OPENAI_API_VERSION", "OPENAI_API_TYPE",
    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT"
):
    os.environ.pop(var, None)

API_KEY = os.getenv("openai_embedding_key")
if not API_KEY:
    logging.error("Missing openai_embedding_key in .env → aborting")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s"
)
logging.info("Using OpenAI key from .env (direct API, no Azure)")

# ────────────────────────────────────────────────────────────────
# 2) PATHS & SPLITTER
# ────────────────────────────────────────────────────────────────
BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT     = BACKEND_ROOT / "Data" / "Interim"
INDEX_DIR    = BACKEND_ROOT / "index"
INDEX_DIR.mkdir(exist_ok=True, parents=True)

splitter = RecursiveCharacterTextSplitter(
    chunk_size    = 2_000,
    chunk_overlap =   200,
)

# ────────────────────────────────────────────────────────────────
# 3) EMBEDDINGS CLIENT
# ────────────────────────────────────────────────────────────────
embedder = OpenAIEmbeddings(
    model          = "text-embedding-ada-002",
    openai_api_key = API_KEY,
)
logging.info("OpenAIEmbeddings ready (model=text-embedding-ada-002)")

# ────────────────────────────────────────────────────────────────
# 4) COLLECT & CHUNK
# ────────────────────────────────────────────────────────────────
docs: list[Document] = []
txt_files = list(SRC_ROOT.rglob("txt/*.txt"))
logging.info("Found %d TXT files under %s", len(txt_files), SRC_ROOT.relative_to(BACKEND_ROOT))

for txt_path in txt_files:
    stem      = txt_path.stem
    company   = txt_path.parent.parent.name
    json_path = txt_path.parent.parent / "json" / f"{stem}.json"
    if not json_path.exists():
        logging.warning("Skipping %s (no JSON metadata)", txt_path.relative_to(BACKEND_ROOT))
        continue

    # load & sanitize metadata
    raw_meta = json.loads(json_path.read_text(encoding="utf-8"))
    # keep only primitives (str,int,float,bool)
    meta = {
        k: v for k, v in {
            **raw_meta,
            "company_slug": company.lower().replace(" ", "-"),
            "source_pdf":   stem + ".pdf",
        }.items()
        if isinstance(v, (str, int, float, bool))
    }
    if len(meta) < len(raw_meta):
        logging.debug("Dropped non-primitive metadata keys in %s", json_path.name)

    # split the P&L text into chunks
    raw_text = txt_path.read_text(encoding="utf-8")
    chunks   = splitter.split_text(raw_text)
    logging.info("  • %s → %d chunks", txt_path.name, len(chunks))
    for c in chunks:
        docs.append(Document(page_content=c, metadata=meta))

logging.info("Total chunks prepared: %d", len(docs))
if not docs:
    logging.error("No chunks to index; exiting.")
    sys.exit(1)

# ────────────────────────────────────────────────────────────────
# 5) BUILD & SAVE CHROMA INDEX
# ────────────────────────────────────────────────────────────────
t0 = perf_counter()
try:
    vectordb = Chroma.from_documents(
        docs,
        embedding         = embedder,
        persist_directory = str(INDEX_DIR),
    )
    vectordb.persist()
    elapsed = perf_counter() - t0
    logging.info("Indexed %d chunks → %s  (%.1f s)",
                 len(docs), INDEX_DIR.relative_to(BACKEND_ROOT), elapsed)
except Exception:
    logging.exception("Failed to build Chroma index")
    sys.exit(1)
