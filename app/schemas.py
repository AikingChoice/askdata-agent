from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    question: str
    route: str = "sql"
    answer: str = ""
    analysis: dict[str, Any] = Field(default_factory=dict)
    selected_tables: list[str] = Field(default_factory=list)
    raw_sql: str = ""
    sql: str | None = None
    guard_ok: bool = False
    guard_reason: str = ""
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    latency_ms: int = 0
    model: str = ""
    attempts: int = 0
    trace: list[str] = Field(default_factory=list)
    error: str | None = None
