"""Drop AI — LLM providers and model registry."""

from drop_ai.client import LLMClient
from drop_ai.errors import ModelUnavailableError
from drop_ai.profiles import apply_max_tokens, capabilities_for, filter_completion_kwargs
from drop_ai.protocol import (
    CompletionRequest,
    CompletionResult,
    LLMProvider,
    Message,
)
from drop_ai.providers.gemini_provider import GeminiProvider
from drop_ai.providers.openai_provider import OpenAIProvider
from drop_ai.refs import DEFAULT_FALLBACK_REFS, parse_fallback_refs, parse_model_ref
from drop_ai.registry import ModelConfig, ModelRegistry, build_registry_from_mapping

__all__ = [
    "DEFAULT_FALLBACK_REFS",
    "CompletionRequest",
    "CompletionResult",
    "GeminiProvider",
    "LLMClient",
    "LLMProvider",
    "Message",
    "ModelConfig",
    "ModelRegistry",
    "ModelUnavailableError",
    "OpenAIProvider",
    "apply_max_tokens",
    "build_registry_from_mapping",
    "capabilities_for",
    "filter_completion_kwargs",
    "parse_fallback_refs",
    "parse_model_ref",
]
