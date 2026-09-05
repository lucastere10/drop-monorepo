from __future__ import annotations

import logging
import time

from drop_ai.errors import ModelUnavailableError
from drop_ai.protocol import CompletionRequest, CompletionResult, LLMProvider
from drop_ai.registry import ModelConfig, ModelRegistry

logger = logging.getLogger("drop_ai")


def _ref(cfg: ModelConfig) -> str:
    return f"{cfg.provider}:{cfg.model}"


class LLMClient:
    """Resolves use → model chain and dispatches with retries + fallback."""

    def __init__(
        self,
        *,
        registry: ModelRegistry,
        providers: dict[str, LLMProvider],
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
    ):
        self.registry = registry
        self.providers = providers
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def complete(self, req: CompletionRequest) -> CompletionResult:
        chain = self.registry.resolve_chain(req["use"])
        last_unavailable: Exception | None = None
        use = req["use"]

        for index, cfg in enumerate(chain):
            next_ref = _ref(chain[index + 1]) if index + 1 < len(chain) else "-"
            using_fallback = index > 0
            provider = self.providers.get(cfg.provider)
            if provider is None:
                last_unavailable = ModelUnavailableError(
                    f"Provider not configured: {cfg.provider}",
                    provider=cfg.provider,
                    model=cfg.model,
                    retryable=False,
                )
                logger.warning(
                    "llm skip use=%s from=%s to=%s reason=provider_not_configured",
                    use,
                    _ref(cfg),
                    next_ref,
                )
                continue

            max_tokens = req.get("max_tokens", cfg.max_tokens)
            response_format = req.get("response_format")
            last_exc: Exception | None = None
            for attempt in range(self.max_retries + 1):
                try:
                    result = provider.complete(
                        model=cfg.model,
                        messages=req["messages"],
                        max_tokens=max_tokens,
                        response_format=response_format,
                    )
                    logger.info(
                        "llm complete use=%s provider=%s model=%s fallback=%s",
                        use,
                        result["provider"],
                        result["model"],
                        "true" if using_fallback else "false",
                    )
                    return result
                except ModelUnavailableError as exc:
                    last_exc = exc
                    if not exc.retryable or attempt >= self.max_retries:
                        break
                    time.sleep(self.backoff_seconds * (attempt + 1))
                except Exception as exc:
                    last_exc = exc
                    if attempt >= self.max_retries:
                        raise
                    time.sleep(self.backoff_seconds * (attempt + 1))

            if isinstance(last_exc, ModelUnavailableError):
                last_unavailable = last_exc
                logger.warning(
                    "llm fallback use=%s from=%s to=%s reason=%s",
                    use,
                    _ref(cfg),
                    next_ref,
                    last_exc,
                )
                continue
            assert last_exc is not None
            raise last_exc

        if last_unavailable is not None:
            raise last_unavailable
        raise RuntimeError("No LLM provider available")
