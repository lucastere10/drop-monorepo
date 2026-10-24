import logging

import pytest
from django.conf import settings
from drop_ai.client import LLMClient
from drop_ai.errors import ModelUnavailableError
from drop_ai.profiles import apply_max_tokens, capabilities_for, filter_completion_kwargs
from drop_ai.refs import DEFAULT_FALLBACK_REFS, parse_fallback_refs, parse_model_ref
from drop_ai.registry import ModelConfig, ModelRegistry, build_registry_from_mapping


def test_registry_resolve():
    reg = build_registry_from_mapping(
        {
            "default": {"provider": "gemini", "model": "gemini-2.5-flash"},
            "uses": {
                "chat": {"provider": "openai", "model": "gpt-4.1-mini", "max_tokens": 100},
            },
        }
    )
    chat = reg.resolve("chat")
    assert chat.provider == "openai"
    assert chat.max_tokens == 100
    overview = reg.resolve("overview")
    assert overview.provider == "gemini"


def test_registry_missing():
    reg = ModelRegistry({"chat": ModelConfig("openai", "gpt")})
    try:
        reg.resolve("overview")
        assert False
    except KeyError:
        assert True


def test_parse_model_ref():
    assert parse_model_ref("openai:gpt-5.6-luna") == ("openai", "gpt-5.6-luna")
    assert parse_model_ref("  Gemini:gemini-3.5-flash  ") == ("gemini", "gemini-3.5-flash")


@pytest.mark.parametrize(
    "raw",
    ["", "gpt-4o-mini", "openai:", ":gpt-4o-mini", "anthropic:claude"],
)
def test_parse_model_ref_rejects_invalid(raw):
    with pytest.raises(ValueError):
        parse_model_ref(raw)


def test_parse_fallback_refs():
    assert parse_fallback_refs("gemini:gemini-3.5-flash,openai:gpt-5.6-luna") == [
        ("gemini", "gemini-3.5-flash"),
        ("openai", "gpt-5.6-luna"),
    ]
    assert parse_fallback_refs("") == []


def test_resolve_chain_applies_code_fallbacks_and_dedupes():
    reg = build_registry_from_mapping(
        {
            "uses": {
                "chat": {"ref": "openai:gpt-5.6-luna", "max_tokens": 2048},
            },
        }
    )
    chain = reg.resolve_chain("chat")
    assert [(c.provider, c.model) for c in chain] == [
        ("openai", "gpt-4o-mini"),
        ("gemini", "gemini-3.5-flash"),
    ]
    assert chain[0].max_tokens == 2048
    assert chain[1].max_tokens == 2048
    assert DEFAULT_FALLBACK_REFS[0] == ("gemini", "gemini-3.5-flash")


def test_explicit_fallbacks_override_code_defaults():
    reg = build_registry_from_mapping(
        {
            "uses": {
                "chat": {
                    "provider": "openai",
                    "model": "gpt-5.6-luna",
                    "fallbacks": ["openai:gpt-4o-mini"],
                },
            },
        }
    )
    chain = reg.resolve_chain("chat")
    assert [(c.provider, c.model) for c in chain] == [
        ("openai", "gpt-5.6-luna"),
        ("openai", "gpt-4o-mini"),
    ]


class _FakeProvider:
    def __init__(self, name: str, behavior):
        self.name = name
        self.behavior = behavior
        self.calls: list[str] = []

    def complete(self, *, model, messages, max_tokens=None, response_format=None):
        self.calls.append(model)
        result = self.behavior(model)
        if isinstance(result, Exception):
            raise result
        return result


def _ok(provider: str, model: str) -> dict:
    return {"content": f"ok:{model}", "provider": provider, "model": model}


def test_client_falls_back_when_model_unavailable(caplog):
    registry = build_registry_from_mapping(
        {
            "uses": {
                "chat": {
                    "ref": "openai:gpt-5.6-luna",
                    "fallbacks": ["gemini:gemini-3.5-flash"],
                }
            },
        }
    )
    openai = _FakeProvider(
        "openai",
        lambda model: ModelUnavailableError(
            "missing", provider="openai", model=model, retryable=False
        ),
    )
    gemini = _FakeProvider("gemini", lambda model: _ok("gemini", model))
    client = LLMClient(
        registry=registry,
        providers={"openai": openai, "gemini": gemini},
        max_retries=0,
        backoff_seconds=0,
    )
    with caplog.at_level(logging.INFO, logger="drop_ai"):
        result = client.complete({"use": "chat", "messages": [{"role": "user", "content": "hi"}]})
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.5-flash"
    assert openai.calls == ["gpt-5.6-luna"]
    assert gemini.calls == ["gemini-3.5-flash"]
    assert "fallback=true" in caplog.text
    assert "from=openai:gpt-5.6-luna" in caplog.text
    assert "to=gemini:gemini-3.5-flash" in caplog.text


def test_client_skips_missing_provider(caplog):
    registry = build_registry_from_mapping(
        {
            "uses": {
                "chat": {
                    "ref": "openai:gpt-5.6-luna",
                    "fallbacks": ["gemini:gemini-3.5-flash"],
                }
            },
        }
    )
    gemini = _FakeProvider("gemini", lambda model: _ok("gemini", model))
    client = LLMClient(
        registry=registry,
        providers={"gemini": gemini},
        max_retries=0,
        backoff_seconds=0,
    )
    with caplog.at_level(logging.INFO, logger="drop_ai"):
        result = client.complete({"use": "chat", "messages": [{"role": "user", "content": "hi"}]})
    assert result["model"] == "gemini-3.5-flash"
    assert "reason=provider_not_configured" in caplog.text
    assert "fallback=true" in caplog.text


def test_client_logs_primary_success(caplog):
    registry = build_registry_from_mapping(
        {"uses": {"chat": {"ref": "openai:gpt-5.6-luna", "fallbacks": []}}}
    )
    openai = _FakeProvider("openai", lambda model: _ok("openai", model))
    client = LLMClient(
        registry=registry,
        providers={"openai": openai},
        max_retries=0,
        backoff_seconds=0,
    )
    with caplog.at_level(logging.INFO, logger="drop_ai"):
        client.complete({"use": "chat", "messages": [{"role": "user", "content": "hi"}]})
    assert "provider=openai" in caplog.text
    assert "model=gpt-4o-mini" in caplog.text
    assert "fallback=false" in caplog.text


def test_client_does_not_fallback_on_other_errors():
    registry = build_registry_from_mapping(
        {
            "uses": {
                "chat": {
                    "ref": "openai:gpt-5.6-luna",
                    "fallbacks": ["gemini:gemini-3.5-flash"],
                }
            },
        }
    )
    openai = _FakeProvider("openai", lambda _model: ValueError("bad request"))
    gemini = _FakeProvider("gemini", lambda model: _ok("gemini", model))
    client = LLMClient(
        registry=registry,
        providers={"openai": openai, "gemini": gemini},
        max_retries=0,
        backoff_seconds=0,
    )
    with pytest.raises(ValueError, match="bad request"):
        client.complete({"use": "chat", "messages": [{"role": "user", "content": "hi"}]})
    assert gemini.calls == []


def test_profile_omits_temperature_for_reasoning_models():
    kwargs = filter_completion_kwargs(
        {"model": "gpt-5.6-luna", "temperature": 0.7},
        provider="openai",
        model="gpt-5.6-luna",
        temperature=0.7,
    )
    assert "temperature" not in kwargs

    kwargs_forced = filter_completion_kwargs(
        {"model": "gpt-5.6-luna", "temperature": 0.2},
        provider="openai",
        model="gpt-5.6-luna",
    )
    assert "temperature" not in kwargs_forced


def test_profile_token_params():
    assert capabilities_for(provider="openai", model="gpt-5.6-luna").token_param == (
        "max_completion_tokens"
    )
    assert apply_max_tokens({}, provider="openai", model="gpt-4o-mini", max_tokens=128) == {
        "max_tokens": 128
    }
    assert apply_max_tokens({}, provider="gemini", model="gemini-3.5-flash", max_tokens=64) == {
        "max_output_tokens": 64
    }
    gpt4o = filter_completion_kwargs(
        {},
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.4,
    )
    assert gpt4o["temperature"] == 0.4


def test_settings_llm_config_is_per_use_case():
    uses = settings.LLM_CONFIG["uses"]
    assert set(uses) == {"overview", "insights", "chat", "charts"}
    for cfg in uses.values():
        assert cfg["provider"]
        assert cfg["model"]
        assert "fallbacks" not in cfg
    assert "default" not in settings.LLM_CONFIG
