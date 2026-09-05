from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from drop_ai.protocol import UseCase
from drop_ai.refs import DEFAULT_FALLBACK_REFS, parse_model_ref


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    max_tokens: int | None = None
    fallbacks: tuple[ModelConfig, ...] = ()


class ModelRegistry:
    """Maps use cases to provider/model configuration."""

    def __init__(self, mapping: dict[str, ModelConfig], default: ModelConfig | None = None):
        self._mapping = mapping
        self._default = default

    def resolve(self, use: UseCase | str) -> ModelConfig:
        if use in self._mapping:
            return self._mapping[use]
        if self._default is not None:
            return self._default
        raise KeyError(f"No model configured for use case: {use}")

    def resolve_chain(self, use: UseCase | str) -> list[ModelConfig]:
        primary = self.resolve(use)
        chain = [
            ModelConfig(
                provider=primary.provider,
                model=primary.model,
                max_tokens=primary.max_tokens,
            )
        ]
        seen = {(primary.provider, primary.model)}
        for fb in primary.fallbacks:
            key = (fb.provider, fb.model)
            if key in seen:
                continue
            seen.add(key)
            chain.append(
                ModelConfig(
                    provider=fb.provider,
                    model=fb.model,
                    max_tokens=fb.max_tokens if fb.max_tokens is not None else primary.max_tokens,
                )
            )
        return chain


def _leaf_config(item: Any) -> ModelConfig:
    if isinstance(item, str):
        provider, model = parse_model_ref(item)
        return ModelConfig(provider=provider, model=model)
    if item.get("ref"):
        provider, model = parse_model_ref(item["ref"])
        return ModelConfig(provider=provider, model=model, max_tokens=item.get("max_tokens"))
    return ModelConfig(
        provider=item["provider"],
        model=item["model"],
        max_tokens=item.get("max_tokens"),
    )


def _default_fallback_configs() -> tuple[ModelConfig, ...]:
    return tuple(ModelConfig(provider=p, model=m) for p, m in DEFAULT_FALLBACK_REFS)


def _config_from_raw(cfg: dict[str, Any]) -> ModelConfig:
    if cfg.get("ref"):
        provider, model = parse_model_ref(cfg["ref"])
    else:
        provider = cfg["provider"]
        model = cfg["model"]

    raw_fallbacks = cfg.get("fallbacks")
    if raw_fallbacks is None:
        fallbacks = _default_fallback_configs()
    else:
        fallbacks = tuple(_leaf_config(item) for item in raw_fallbacks)

    return ModelConfig(
        provider=provider,
        model=model,
        max_tokens=cfg.get("max_tokens"),
        fallbacks=fallbacks,
    )


def build_registry_from_mapping(raw: dict[str, Any]) -> ModelRegistry:
    """
    raw shape:
      {
        "default": {"provider": "openai", "model": "gpt-4o-mini"},
        "uses": {
          "chat": {"ref": "openai:gpt-4.1-mini", "max_tokens": 2048},
          ...
        }
      }

    Fallbacks default to DEFAULT_FALLBACK_REFS unless ``fallbacks`` is set.
    """
    default_raw = raw.get("default") or {}
    default = None
    if default_raw.get("provider") or default_raw.get("ref"):
        default = _config_from_raw(default_raw)

    uses: dict[str, ModelConfig] = {}
    for key, cfg in (raw.get("uses") or {}).items():
        uses[key] = _config_from_raw(cfg)
    return ModelRegistry(uses, default=default)
