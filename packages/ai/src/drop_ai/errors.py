from __future__ import annotations


class ModelUnavailableError(Exception):
    """The requested model cannot be used right now (missing, 404, overloaded)."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str,
        retryable: bool = False,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.retryable = retryable
        self.cause = cause


_NOT_FOUND_MARKERS = (
    "not found",
    "does not exist",
    "model_not_found",
    "not_found",
    "unknown model",
    "invalid model",
)
_OVERLOAD_MARKERS = (
    "overloaded",
    "unavailable",
    "temporarily unavailable",
    "capacity",
    "rate limit",
    "too many requests",
)


def classify_http_error(
    exc: Exception,
    *,
    provider: str,
    model: str,
    status_code: int | None = None,
) -> ModelUnavailableError | None:
    """Map provider HTTP errors to ModelUnavailableError; None means do not fallback."""
    msg = str(exc).lower()
    code = status_code

    if code == 404 or any(marker in msg for marker in _NOT_FOUND_MARKERS):
        return ModelUnavailableError(
            f"Model unavailable: {provider}:{model}",
            provider=provider,
            model=model,
            retryable=False,
            cause=exc,
        )
    if code in {429, 503, 529} or any(marker in msg for marker in _OVERLOAD_MARKERS):
        return ModelUnavailableError(
            f"Model overloaded: {provider}:{model}",
            provider=provider,
            model=model,
            retryable=True,
            cause=exc,
        )
    return None
