from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from rag.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from rag.schemas import AssistantReply

logger = logging.getLogger(__name__)


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        format="json",
    )


def parse_reply(raw: str) -> AssistantReply:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        data = json.loads(match.group(0))
    return AssistantReply.model_validate(data)


def generate(system: str, user: str) -> AssistantReply:
    llm = get_llm()
    message = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )
    content = message.content if isinstance(message.content, str) else str(message.content)
    try:
        return parse_reply(content)
    except Exception:
        logger.exception("Failed to parse model JSON")
        return AssistantReply(
            status="insufficient",
            answer=(
                "I retrieved relevant passages but could not produce a reliable "
                "structured answer. Please try rephrasing the question."
            ),
            confidence=0.1,
        )
