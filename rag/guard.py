from __future__ import annotations

import re

from rag.schemas import AssistantReply

_REFUSAL_PATTERNS = [
    re.compile(r"bypass.{0,40}approval", re.I),
    re.compile(r"ignore.{0,40}polic", re.I),
    re.compile(r"repeat.{0,40}instructions.{0,40}word for word", re.I),
    re.compile(r"print.{0,20}(your|the).{0,20}system prompt", re.I),
    re.compile(r"reveal.{0,20}(your|the).{0,20}(system |hidden )?prompt", re.I),
    re.compile(r"disregard.{0,20}(previous|your) instructions", re.I),
]


REFUSAL_MESSAGE = (
    "I cannot help with that request. I only answer questions about Cerulean "
    "Systems documents that are in scope for this assistant."
)


def user_guard(question: str) -> AssistantReply | None:
    text = question.strip()
    for pat in _REFUSAL_PATTERNS:
        if pat.search(text):
            return AssistantReply(
                status="refused",
                answer=REFUSAL_MESSAGE,
                citations=[],
                conflicts=[],
                confidence=1.0,
            )
    return None
