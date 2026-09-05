from __future__ import annotations

KNOWN_PROVIDERS = frozenset({"openai", "gemini"})

DEFAULT_FALLBACK_REFS: tuple[tuple[str, str], ...] = (
    ("gemini", "gemini-3.5-flash"),
    ("openai", "gpt-4o-mini"),
)


def parse_model_ref(raw: str) -> tuple[str, str]:
    """Parse ``provider:model`` (e.g. ``openai:gpt-5.6-luna``)."""
    value = (raw or "").strip()
    if ":" not in value:
        raise ValueError(f"Invalid model ref {raw!r}; expected provider:model")
    provider, _, model = value.partition(":")
    provider = provider.strip().lower()
    model = model.strip()
    if not provider or not model:
        raise ValueError(f"Invalid model ref {raw!r}; expected provider:model")
    if provider not in KNOWN_PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}; expected openai or gemini")
    return provider, model


def parse_fallback_refs(raw: str) -> list[tuple[str, str]]:
    """Parse a comma-separated list of ``provider:model`` refs."""
    refs: list[tuple[str, str]] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        refs.append(parse_model_ref(part))
    return refs
