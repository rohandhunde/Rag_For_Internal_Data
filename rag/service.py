from __future__ import annotations

from rag.config import AS_OF_DATE
from rag.generate import generate
from rag.guard import user_guard
from rag.prompts import system_prompt, wrap_untrusted_passages
from rag.retrieve import index_exists, retrieve
from rag.schemas import AssistantReply


def ask(question: str) -> AssistantReply:
    blocked = user_guard(question)
    if blocked:
        return blocked

    if not index_exists():
        return AssistantReply(
            status="insufficient",
            answer="The knowledge base has not been ingested yet. Run python -m rag.ingest.",
            confidence=0.0,
        )

    docs = retrieve(question)
    if not docs:
        return AssistantReply(
            status="insufficient",
            answer="No relevant passages were retrieved from the Cerulean Systems corpus.",
            confidence=0.0,
        )

    context = wrap_untrusted_passages(docs)
    user = (
        f"As-of date: {AS_OF_DATE.isoformat()}\n"
        f"User question: {question}\n\n"
        f"Retrieved passages:\n{context}\n\n"
        "Respond with JSON only."
    )
    reply = generate(system_prompt(), user)
    allowed = {str(d.metadata.get("document_id", "")) for d in docs}
    reply.citations = [
        c for c in reply.citations if c.document_id in allowed
    ]
    return reply
