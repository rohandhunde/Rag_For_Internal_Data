from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    title: str
    version: str
    effective_date: str
    page: int | None = None


class ConflictNote(BaseModel):
    topic: str
    sides: list[str]
    resolution: str


class AssistantReply(BaseModel):
    status: Literal[
        "answer", "insufficient", "conflict", "clarification", "refused"
    ]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    conflicts: list[ConflictNote] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class QueryRequest(BaseModel):
    question: str
