from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rag.config import AS_OF_DATE, OLLAMA_MODEL
from rag.ingest import ingest_corpus
from rag.retrieve import clear_index_cache, index_exists
from rag.schemas import AssistantReply, QueryRequest
from rag.service import ask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not index_exists():
        logger.info("No vector index found; ingesting corpus on startup")
        ingest_corpus()
        clear_index_cache()
    yield


app = FastAPI(
    title="Cerulean Systems grounded RAG assistant",
    description="SAITC Applied AI Engineer take-home: answers grounded in the official corpus.",
    version="1.0.0",
    lifespan=lifespan,
)


class IngestResponse(BaseModel):
    chunks: int
    documents: list[str]
    vectorstore: str


@app.get("/health")
def health():
    return {
        "ok": True,
        "as_of_date": AS_OF_DATE.isoformat(),
        "model": OLLAMA_MODEL,
        "index_ready": index_exists(),
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    try:
        result = ingest_corpus()
        clear_index_cache()
        return result
    except Exception as exc:
        logger.exception("Ingest failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask", response_model=AssistantReply)
def ask_endpoint(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    return ask(request.question)
