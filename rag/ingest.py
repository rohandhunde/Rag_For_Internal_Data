from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from rag.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CORPUS_DIR,
    EMBEDDING_MODEL,
    FAISS_DIR,
    PASSAGES_PATH,
    VECTORSTORE_DIR,
)
from rag.metadata import iter_corpus_pdfs, load_manifest, parse_header_metadata

logger = logging.getLogger(__name__)

SECTION_SPLIT = re.compile(r"\n(?=\d+(?:\.\d+)*\s+[A-Z])")


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def _read_pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((i, text))
    return pages


def _split_keep_tables(text: str) -> list[str]:
    parts = [p.strip() for p in SECTION_SPLIT.split(text) if p.strip()]
    if len(parts) <= 1:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " "],
        )
        return splitter.split_text(text)

    out: list[str] = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " "],
    )
    for part in parts:
        if len(part) <= CHUNK_SIZE:
            out.append(part)
        else:
            out.extend(splitter.split_text(part))
    return out


def build_documents(corpus_dir: Path | None = None) -> list[Document]:
    corpus_dir = corpus_dir or CORPUS_DIR
    manifest = load_manifest(corpus_dir)
    docs: list[Document] = []

    for path in iter_corpus_pdfs(corpus_dir):
        pages = _read_pdf_pages(path)
        full_text = "\n".join(t for _, t in pages)
        header = parse_header_metadata(full_text)
        row = manifest.get(path.name, {})
        meta = {
            "source": path.name,
            "document_id": row.get("document_id") or header.get("document_id") or path.stem,
            "title": row.get("title") or path.stem,
            "version": str(row.get("version") or header.get("version") or ""),
            "effective_date": row.get("effective_date") or header.get("effective_date") or "",
            "owner": row.get("owner") or header.get("owner") or "",
            "classification": row.get("classification") or header.get("classification") or "",
            "supersedes": row.get("supersedes") or header.get("supersedes") or "",
        }

        for page_num, page_text in pages:
            if not page_text.strip():
                continue
            for chunk in _split_keep_tables(page_text):
                prefix = (
                    f"Document {meta['document_id']} | {meta['title']} | "
                    f"version {meta['version']} | effective {meta['effective_date']}\n"
                )
                docs.append(
                    Document(
                        page_content=prefix + chunk,
                        metadata={**meta, "page": page_num},
                    )
                )
    return docs


def ingest_corpus(corpus_dir: Path | None = None) -> dict:
    corpus_dir = corpus_dir or CORPUS_DIR
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    documents = build_documents(corpus_dir)
    if not documents:
        raise RuntimeError("No documents were ingested. Check the corpus folder.")

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    db = FAISS.from_documents(documents, embeddings)
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    db.save_local(str(FAISS_DIR))

    passages = []
    for i, doc in enumerate(documents):
        passages.append(
            {
                "id": i,
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
        )
    PASSAGES_PATH.write_text(json.dumps(passages, indent=2), encoding="utf-8")

    ids = sorted({d.metadata["document_id"] for d in documents})
    logger.info("Ingested %s chunks from %s documents", len(documents), len(ids))
    return {
        "chunks": len(documents),
        "documents": ids,
        "vectorstore": str(FAISS_DIR),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = ingest_corpus()
    print(json.dumps(result, indent=2))
