from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

TokenParam = Literal["max_tokens", "max_completion_tokens", "max_output_tokens"]


@dataclass(frozen=True)
class ModelCapabilities:
    supports_temperature: bool = False
    token_param: TokenParam = "max_tokens"


def capabilities_for(*, provider: str, model: str) -> ModelCapabilities:
    """Conservative defaults: omit temperature unless the family is known to accept it."""
    name = model.lower()
    if provider == "openai":
        if any(marker in name for marker in ("gpt-5", "gpt-4.1", "o1", "o3", "o4")):
            return ModelCapabilities(supports_temperature=False, token_param="max_completion_tokens")
        if "gpt-4o" in name:
            return ModelCapabilities(supports_temperature=True, token_param="max_tokens")
        return ModelCapabilities(supports_temperature=False, token_param="max_tokens")
    if provider == "gemini":
        return ModelCapabilities(supports_temperature=False, token_param="max_output_tokens")
    return ModelCapabilities(supports_temperature=False, token_param="max_tokens")


def filter_completion_kwargs(
    kwargs: dict[str, Any],
    *,
    provider: str,
    model: str,
    temperature: float | None = None,
) -> dict[str, Any]:
    """Drop unsupported sampling params. Temperature is never forced."""
    caps = capabilities_for(provider=provider, model=model)
    out = {key: value for key, value in kwargs.items() if key != "temperature"}
    if temperature is not None and caps.supports_temperature:
        out["temperature"] = temperature
    return out


def apply_max_tokens(
    kwargs: dict[str, Any],
    *,
    provider: str,
    model: str,
    max_tokens: int | None,
) -> dict[str, Any]:
    out = dict(kwargs)
    for key in ("max_tokens", "max_completion_tokens", "max_output_tokens"):
        out.pop(key, None)
    if max_tokens is None:
        return out
    caps = capabilities_for(provider=provider, model=model)
    out[caps.token_param] = max_tokens
    return out
