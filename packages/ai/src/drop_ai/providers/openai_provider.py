from __future__ import annotations

from typing import Any

from openai import OpenAI

from drop_ai.errors import classify_http_error
from drop_ai.profiles import apply_max_tokens, filter_completion_kwargs
from drop_ai.protocol import CompletionResult, Message


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._client = OpenAI(api_key=api_key)

    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        kwargs = filter_completion_kwargs(
            {"model": model, "messages": messages},
            provider=self.name,
            model=model,
        )
        kwargs = apply_max_tokens(
            kwargs, provider=self.name, model=model, max_tokens=max_tokens
        )
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001 — classify SDK errors
            msg = str(exc).lower()
            if max_tokens is not None and "max_tokens" in msg and "max_completion_tokens" in msg:
                kwargs.pop("max_tokens", None)
                kwargs["max_completion_tokens"] = max_tokens
                try:
                    resp = self._client.chat.completions.create(**kwargs)
                except Exception as retry_exc:  # noqa: BLE001 — classify SDK errors
                    self._raise_classified(retry_exc, model)
            else:
                self._raise_classified(exc, model)

        choice = resp.choices[0].message
        usage = resp.usage
        content = choice.content or ""
        result: CompletionResult = {
            "content": content,
            "provider": self.name,
            "model": model,
        }
        if usage is not None:
            result["input_tokens"] = usage.prompt_tokens or 0
            result["output_tokens"] = usage.completion_tokens or 0
        return result

    def _raise_classified(self, exc: Exception, model: str) -> None:
        status = getattr(exc, "status_code", None)
        wrapped = classify_http_error(exc, provider=self.name, model=model, status_code=status)
        if wrapped is not None:
            raise wrapped from exc
        raise exc
