

# backend/app.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from langchain_openai import AzureChatOpenAI, OpenAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import HumanMessage

# ───────────────────────── 1) Load .env & Logging ─────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s"
)
logger = logging.getLogger("chat-api")
logger.info("Starting Chat API")

# ───────────────────── 2) Public OpenAI Embeddings ────────────────────────
embed_key = os.getenv("OPENAI_EMBEDDING_KEY") or os.getenv("openai_embedding_key")
if not embed_key:
    logger.error("Missing OPENAI_EMBEDDING_KEY in .env")
    raise RuntimeError("Missing OPENAI_EMBEDDING_KEY in .env")

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=embed_key,
)
logger.info("OpenAIEmbeddings initialized")

# ───────────────────── 3) Chroma Vector Store ─────────────────────────────
# index_dir = Path(os.getenv("INDEX_DIR", "backend/index"))
# always points to backend/index next to app.py
index_dir = Path(__file__).resolve().parent / "index"

vectordb = Chroma(
    persist_directory=str(index_dir),
    embedding_function=embeddings,
)
if not index_dir.exists() or not any(index_dir.iterdir()):
    logger.warning("Chroma index folder is empty: %s", index_dir)
else:
    logger.info("Loaded Chroma index from %s", index_dir)

retriever = vectordb.as_retriever(search_kwargs={"k": 4})

# ───────────────────── 4) OpenAI Chat LLM ─────────────────────────────────
chat_key = os.getenv("OPENAI_API_KEY") or embed_key
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=chat_key,
    temperature=0.0,
)
logger.info("ChatOpenAI initialized (model=gpt-3.5-turbo)")

SYSTEM_PROMPT = (
    "You are a concise financial-statement assistant. "
    "Answer only from the supplied context. "
    "If the answer is not present, say 'I don't know'."
)


# # ───────────────────────── 1) Load .env & Logging ─────────────────────────
# load_dotenv(Path(__file__).parent.parent / ".env")
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)-8s %(message)s"
# )
# logger = logging.getLogger("chat-api")
# logger.info("Starting Chat API")

# # ──────────────────── 1.1) Scrub any Azure vars for embeddings ─────────────
# for v in (
#     "OPENAI_API_BASE", "OPENAI_API_TYPE", "OPENAI_API_VERSION",
#     "AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"
# ):
#     os.environ.pop(v, None)

# # ───────────────────── 2) Public OpenAI Embeddings ────────────────────────
# embed_key = os.getenv("openai_embedding_key") or os.getenv("OPENAI_EMBEDDING_KEY")
# if not embed_key:
#     logger.error("Missing openai_embedding_key in .env")
#     raise RuntimeError("Missing openai_embedding_key in .env")

# embeddings = OpenAIEmbeddings(
#     model="text-embedding-ada-002",
#     openai_api_key=embed_key,
# )
# logger.info("OpenAIEmbeddings initialized")

# # ───────────────────── 3) Chroma Vector Store ─────────────────────────────
# index_dir = Path(os.getenv("INDEX_DIR", "backend/index"))
# vectordb = Chroma(
#     persist_directory=str(index_dir),
#     embedding_function=embeddings,
# )
# if not index_dir.exists() or not any(index_dir.iterdir()):
#     logger.warning("Chroma index folder is empty: %s", index_dir)
# else:
#     logger.info("Loaded Chroma index from %s", index_dir)

# retriever = vectordb.as_retriever(search_kwargs={"k": 4})

# # ───────────────────── 4) Azure Chat LLM ─────────────────────────────────
# # (we scrubbed Azure vars above, now re-load them for the chat client)
# load_dotenv(Path(__file__).parent.parent / ".env")

# azure_base   = os.getenv("OPENAI_API_BASE")
# azure_key    = os.getenv("AZURE_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
# azure_deploy = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("OPENAI_MODEL")
# azure_ver    = os.getenv("OPENAI_API_VERSION", "2024-06-01-preview")

# if not all([azure_base, azure_key, azure_deploy]):
#     logger.error(
#         "Azure configuration missing. "
#         "OPENAI_API_BASE=%s AZURE_OPENAI_KEY set?=%s AZURE_OPENAI_DEPLOYMENT=%s",
#         azure_base, bool(azure_key), azure_deploy
#     )
#     raise RuntimeError(
#         "Need OPENAI_API_BASE, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT in .env"
#     )

# llm = AzureChatOpenAI(
#     azure_endpoint     = azure_base,
#     azure_api_key      = azure_key,
#     azure_deployment   = azure_deploy,
#     openai_api_version = azure_ver,
#     temperature        = 0.0,
# )
# logger.info("AzureChatOpenAI initialized (deployment=%s)", azure_deploy)

# SYSTEM_PROMPT = (
#     "You are a concise financial-statement assistant. "
#     "Answer only from the supplied context. "
#     "If the answer is not present, say 'I don't know'."
# )

# ───────────────────── 5) FastAPI Setup ──────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    company:  str
    question: str

class ChatResponse(BaseModel):
    answer:  str
    sources: list[str]

@app.get("/")
def health_check():
    return {"status": "ok"}

# @app.post("/api/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     logger.info("API /api/chat  company=%s  question=%s", req.company, req.question)

#     # 1) Vector search
#     try:
#         docs = retriever.get_relevant_documents(req.question)
#     except Exception as e:
#         logger.exception("Vector search error")
#         raise HTTPException(status_code=500, detail="Vector search failed")

#     # 2) Filter by company & chunk
#     chosen = [d.page_content for d in docs if d.metadata.get("company_slug")==req.company][:4]
#     logger.info("Chunks after filter: %d", len(chosen))
#     context = "\n---\n".join(chosen) or "No relevant context."

#     # 3) Prompt Azure LLM
#     prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser: {req.question}"
#     try:
#         resp = llm([HumanMessage(content=prompt)])
#     except Exception:
#         logger.exception("LLM generation error")
#         raise HTTPException(status_code=500, detail="LLM generation failed")

#     # 4) Build sources list
#     sources = [
#         d.metadata.get("source_pdf","unknown")
#         for d in docs
#         if d.metadata.get("company_slug")==req.company
#     ][:4]

#     return ChatResponse(answer=resp.content, sources=sources)

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1) Vector search + metadata filter in one go
    try:
        docs = vectordb.similarity_search(
            req.question,
            k=4,
            filter={"company_slug": req.company}
        )
    except Exception:
        logger.exception("Vector search error")
        raise HTTPException(status_code=500, detail="Vector search failed")

    logger.info("Docs after filter: %s", [d.metadata for d in docs])

    # 2) Build context
    context = "\n---\n".join(d.page_content for d in docs) or "No relevant context."

    # 3) LLM call
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser: {req.question}"
    try:
        resp = llm([HumanMessage(content=prompt)])
    except Exception:
        logger.exception("LLM generation error")
        raise HTTPException(status_code=500, detail="LLM generation failed")

    # 4) Build sources
    sources = [d.metadata.get("source_pdf", "unknown") for d in docs]

    return ChatResponse(answer=resp.content, sources=sources)


@app.get("/api/slugs")
def list_slugs():
    # grab everything from Chroma
    data = vectordb._collection.get(include=["metadatas"], limit=1000)
    slugs = sorted({m["company_slug"] for m in data["metadatas"]})
    return {"company_slugs": slugs}

