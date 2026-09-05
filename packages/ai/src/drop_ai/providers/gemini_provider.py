from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from drop_ai.errors import classify_http_error
from drop_ai.profiles import apply_max_tokens, filter_completion_kwargs
from drop_ai.protocol import CompletionResult, Message


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._client = genai.Client(api_key=api_key)

    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> CompletionResult:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        contents: list[types.Content] = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
            )

        config_kwargs = filter_completion_kwargs({}, provider=self.name, model=model)
        config_kwargs = apply_max_tokens(
            config_kwargs, provider=self.name, model=model, max_tokens=max_tokens
        )
        if system_parts:
            config_kwargs["system_instruction"] = "\n\n".join(system_parts)
        if response_format is not None:
            config_kwargs["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
        try:
            resp = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 — classify SDK errors
            status = getattr(exc, "code", None)
            wrapped = classify_http_error(exc, provider=self.name, model=model, status_code=status)
            if wrapped is not None:
                raise wrapped from exc
            raise

        text = resp.text or ""
        result: CompletionResult = {
            "content": text,
            "provider": self.name,
            "model": model,
        }
        usage = getattr(resp, "usage_metadata", None)
        if usage is not None:
            result["input_tokens"] = getattr(usage, "prompt_token_count", 0) or 0
            result["output_tokens"] = getattr(usage, "candidates_token_count", 0) or 0
        return result
