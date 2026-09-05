from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from drop_ai.protocol import Message


class AnalysisToolset(Protocol):
    def schema(self) -> list[dict[str, Any]]: ...

    def stats(self) -> dict[str, Any]: ...

    def sample(self, n: int = 5) -> list[dict[str, Any]]: ...

    def aggregate(self, column: str, fn: str = "sum") -> Any: ...


@dataclass
class AgentContext:
    analysis_id: UUID
    goal: str
    messages: list[Message] = field(default_factory=list)
    tools: AnalysisToolset | None = None
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


class AgentRunner(Protocol):
    def run(self, ctx: AgentContext) -> AgentResult: ...
