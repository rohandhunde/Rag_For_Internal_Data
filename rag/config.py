from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

AS_OF_DATE = date.fromisoformat(os.getenv("AS_OF_DATE", "2026-08-27"))
CORPUS_DIR = Path(os.getenv("CORPUS_DIR", ROOT / "corpus"))
VECTORSTORE_DIR = Path(os.getenv("VECTORSTORE_DIR", ROOT / "data" / "vectorstore"))
FAISS_DIR = VECTORSTORE_DIR / "faiss"
PASSAGES_PATH = VECTORSTORE_DIR / "passages.json"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
RETRIEVE_K = int(os.getenv("RETRIEVE_K", "10"))
SEMANTIC_K = 16
BM25_K = 16

# Skip assignment briefing PDF; it is not part of the company knowledge base.
SKIP_FILES = {
    "00_README_Corpus_Overview.pdf",
    "corpus_manifest.json",
}
