from __future__ import annotations

from django.conf import settings
from drop_ai import GeminiProvider, LLMClient, OpenAIProvider, build_registry_from_mapping


def get_llm_client() -> LLMClient:
    registry = build_registry_from_mapping(settings.LLM_CONFIG)
    providers = {}
    if settings.OPENAI_API_KEY:
        providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)
    if settings.GEMINI_API_KEY:
        providers["gemini"] = GeminiProvider(settings.GEMINI_API_KEY)
    return LLMClient(registry=registry, providers=providers)
