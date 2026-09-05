from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from rag.config import CORPUS_DIR, SKIP_FILES


def load_manifest(corpus_dir: Path | None = None) -> dict[str, dict]:
    corpus_dir = corpus_dir or CORPUS_DIR
    path = corpus_dir / "corpus_manifest.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    by_file = {}
    for doc in data.get("documents", []):
        by_file[doc["file"]] = doc
    return by_file


def parse_header_metadata(text: str) -> dict:
    """Fallback parser if a PDF is ingested without a manifest row."""
    meta: dict = {}
    patterns = {
        "document_id": r"Document ID\s+([A-Z0-9-]+)",
        "version": r"Version\s+([0-9.]+)",
        "owner": r"Owner\s+(.+)",
        "classification": r"Classification\s+(\w+)",
        "supersedes": r"Supersedes\s+(.+)",
    }
    for key, pat in patterns.items():
        match = re.search(pat, text)
        if match:
            meta[key] = match.group(1).strip().split("\n")[0]
    date_match = re.search(
        r"Effective Date\s+(\d{1,2}\s+\w+\s+\d{4}|\d{4}-\d{2}-\d{2})", text
    )
    if date_match:
        raw = date_match.group(1).strip()
        meta["effective_date"] = _normalise_date(raw)
    return meta


def _normalise_date(raw: str) -> str:
    raw = raw.strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        pass
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", raw, re.I)
    if not m:
        return raw
    day, month_name, year = m.groups()
    month = months.get(month_name.lower())
    if not month:
        return raw
    return date(int(year), month, int(day)).isoformat()


def iter_corpus_pdfs(corpus_dir: Path | None = None) -> list[Path]:
    corpus_dir = corpus_dir or CORPUS_DIR
    files = []
    for path in sorted(corpus_dir.glob("*.pdf")):
        if path.name in SKIP_FILES:
            continue
        files.append(path)
    return files
