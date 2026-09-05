from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.ingest import ingest_corpus
from rag.retrieve import clear_index_cache, index_exists
from rag.service import ask

QUESTIONS = Path(__file__).parent / "questions.json"
RESULTS_JSON = Path(__file__).parent / "results.json"
RESULTS_MD = Path(__file__).parent / "results.md"


def run() -> None:
    if not index_exists():
        ingest_corpus()
        clear_index_cache()

    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    rows = []
    for item in items:
        started = time.perf_counter()
        reply = ask(item["question"])
        elapsed = time.perf_counter() - started
        payload = reply.model_dump()
        payload["id"] = item["id"]
        payload["question"] = item["question"]
        payload["looking_for"] = item["looking_for"]
        payload["latency_seconds"] = round(elapsed, 2)
        rows.append(payload)
        print(f"Q{item['id']} [{payload['status']}] {elapsed:.1f}s")

    RESULTS_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    RESULTS_MD.write_text(_to_markdown(rows), encoding="utf-8")
    print(f"Wrote {RESULTS_JSON} and {RESULTS_MD}")


def _to_markdown(rows: list[dict]) -> str:
    lines = [
        "# Evaluation results",
        "",
        "Official SAITC questions run against the Cerulean Systems corpus.",
        "",
        "| # | Status | Confidence | Latency (s) | Citations |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        cites = ", ".join(
            sorted({c["document_id"] for c in row.get("citations") or []})
        ) or "—"
        lines.append(
            f"| {row['id']} | {row['status']} | {row.get('confidence', 0):.2f} | "
            f"{row['latency_seconds']} | {cites} |"
        )
    lines.append("")
    for row in rows:
        lines.extend(
            [
                f"## Q{row['id']}. {row['question']}",
                "",
                f"**Looking for:** {row['looking_for']}",
                "",
                f"**Status:** `{row['status']}` · **confidence:** {row.get('confidence', 0)}",
                "",
                row.get("answer") or "",
                "",
            ]
        )
        if row.get("conflicts"):
            lines.append("**Conflicts recorded:**")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(row["conflicts"], indent=2))
            lines.append("```")
            lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-ingest", action="store_true")
    args = parser.parse_args()
    if not args.skip_ingest and not index_exists():
        ingest_corpus()
        clear_index_cache()
    run()
