from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from rag.config import BM25_K, FAISS_DIR, PASSAGES_PATH, RETRIEVE_K, SEMANTIC_K
from rag.ingest import get_embeddings


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().replace("|", " ").split() if t]


@lru_cache(maxsize=1)
def _load_passages() -> list[dict]:
    if not PASSAGES_PATH.exists():
        raise FileNotFoundError(
            "No index found. Run `python -m rag.ingest` first."
        )
    return json.loads(PASSAGES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_faiss() -> FAISS:
    return FAISS.load_local(
        str(FAISS_DIR),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


@lru_cache(maxsize=1)
def _load_bm25() -> tuple[BM25Okapi, list[dict]]:
    passages = _load_passages()
    tokenized = [_tokenize(p["text"]) for p in passages]
    return BM25Okapi(tokenized), passages


def index_exists() -> bool:
    return FAISS_DIR.exists() and PASSAGES_PATH.exists()


def clear_index_cache() -> None:
    _load_passages.cache_clear()
    _load_faiss.cache_clear()
    _load_bm25.cache_clear()


def _rrf(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = defaultdict(float)
    for ranking in rank_lists:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] += 1.0 / (k + rank + 1)
    return [i for i, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


def retrieve(question: str, k: int | None = None) -> list[Document]:
    k = k or RETRIEVE_K
    db = _load_faiss()
    bm25, passages = _load_bm25()

    semantic = db.similarity_search(question, k=SEMANTIC_K)
    semantic_ids: list[int] = []
    seen = set()
    text_to_id = {p["text"]: p["id"] for p in passages}
    for doc in semantic:
        pid = text_to_id.get(doc.page_content)
        if pid is not None and pid not in seen:
            seen.add(pid)
            semantic_ids.append(pid)

    bm25_scores = bm25.get_scores(_tokenize(question))
    bm25_ids = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:BM25_K]

    fused = _rrf([semantic_ids, bm25_ids])[:k]
    results: list[Document] = []
    by_id = {p["id"]: p for p in passages}
    for pid in fused:
        row = by_id[pid]
        results.append(Document(page_content=row["text"], metadata=row["metadata"]))
    return results
