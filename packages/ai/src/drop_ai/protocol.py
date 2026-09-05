from __future__ import annotations

from typing import Any, Literal, NotRequired, Protocol, TypedDict


Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


UseCase = Literal[
    "overview",
    "insights",
    "chat",
    "charts",
    "agent_plan",
]


class CompletionRequest(TypedDict):
    use: UseCase
    messages: list[Message]
    max_tokens: NotRequired[int]
    response_format: NotRequired[dict[str, Any]]


class CompletionResult(TypedDict):
    content: str
    provider: str
    model: str
    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]


class LLMProvider(Protocol):
    name: str

    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult: ...
