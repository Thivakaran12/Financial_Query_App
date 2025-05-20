# backend/app.py
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_openai import OpenAIEmbeddings  
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import HumanMessage

# ─── Paths & Logging ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logger.info("Starting Chat API")

# ─── FastAPI setup ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Financial P&L Chat API",
    description="Query quarterly P&L statements via vector search + LLM",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request / Response Models ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    company: str = Field(..., alias="company_slug")
    question: str
    history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# ─── Load system prompt from Jinja2 template ─────────────────────────────────
tmpl_env = Environment(
    loader=FileSystemLoader(str(PROJECT_ROOT)),
    autoescape=select_autoescape([]),
)
SYSTEM_PROMPT = tmpl_env.get_template("system_prompt.j2").render()
logger.info("Loaded system prompt from system_prompt.j2")

# ─── OpenAI Embeddings & Chroma DB ───────────────────────────────────────────
EMBED_KEY = os.getenv("OPENAI_EMBEDDING_KEY") or os.getenv("openai_embedding_key")
if not EMBED_KEY:
    logger.error("Missing OPENAI_EMBEDDING_KEY in .env")
    sys.exit(1)

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=EMBED_KEY,
)
logger.info("OpenAIEmbeddings initialized")

INDEX_DIR = PROJECT_ROOT.parent / "data" / "index"
vectordb = Chroma(
    persist_directory=str(INDEX_DIR),
    embedding_function=embeddings
)
logger.info("Chroma index loaded from %s", INDEX_DIR)

# ─── LLM Setup ───────────────────────────────────────────────────────────────
CHAT_KEY = os.getenv("OPENAI_API_KEY") or EMBED_KEY
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=CHAT_KEY,
    temperature=0.0,
)
logger.info("ChatOpenAI initialized (model=gpt-3.5-turbo)")

# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
def chat(req: ChatRequest):
    # 1) Vector search + filter by company_slug
    try:
        docs = vectordb.similarity_search(
            req.question,
            k=4,
            filter={"company_slug": req.company}
        )
    except Exception:
        logger.exception("Vector search failed for %s", req.company)
        raise HTTPException(status_code=500, detail="Vector search failed")

    logger.info("Vector search returned %d docs for %s", len(docs), req.company)

    # 2) Build a single context string
    context = "\n---\n".join(d.page_content for d in docs) or "No relevant context."

    # 3) Render final prompt = system + context + history + user
    #   (you can also inject `req.history` for multi‐turn chaining)
    full_prompt = "\n\n".join([
        SYSTEM_PROMPT,
        "Context:\n" + context,
        f"User: {req.question}"
    ])
    try:
        resp = llm([HumanMessage(content=full_prompt)])
    except Exception:
        logger.exception("LLM generation failed")
        raise HTTPException(status_code=500, detail="LLM generation failed")

    # 4) Return both answer and source filenames
    sources = [d.metadata.get("source_txt", "unknown") for d in docs]
    return ChatResponse(answer=resp.content, sources=sources)

@app.get("/api/slugs", tags=["metadata"])
def list_slugs():
    data = vectordb._collection.get(include=["metadatas"], limit=1000)
    slugs = sorted({m["company_slug"] for m in data["metadatas"]})
    return {"company_slugs": slugs}
