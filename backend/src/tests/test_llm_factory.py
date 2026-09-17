"""Tests for :mod:`src.core.llm` — the lazy, memoized provider factory.

Building a chat model only *stores* its configuration; the first real HTTP
request happens at invoke time, so these tests never touch Ollama or any
network endpoint. ``PROVIDER`` is read at import time, so it is patched via
``monkeypatch.setattr`` (not ``setenv``) and the cache is cleared with
``llm.reset()`` around every test.
"""

from __future__ import annotations

import pytest
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from src.core import llm


@pytest.fixture(autouse=True)
def _clear_model_cache():
    """Clear the module-level instance cache around every test."""
    llm.reset()
    yield
    llm.reset()


def test_unknown_provider_raises_value_error(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "bogus")
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER 'bogus'"):
        llm.build_chat_model()


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "openai")
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "")
    with pytest.raises(RuntimeError, match="requires OPENAI_API_KEY"):
        llm.build_chat_model()


def test_local_provider_builds_ollama_model(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "local")
    assert isinstance(llm.build_chat_model("qwen2.5:7b"), ChatOllama)


def test_openai_provider_builds_model_when_key_present(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "openai")
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "sk-test-key")
    assert isinstance(llm.build_chat_model("deepseek-flash"), ChatOpenAI)


def test_cache_returns_same_instance(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "local")
    assert llm.build_chat_model("qwen2.5:7b") is llm.build_chat_model("qwen2.5:7b")


def test_provider_switch_isolates_cache(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "local")
    local = llm.build_chat_model("qwen2.5:7b")

    monkeypatch.setattr(llm, "PROVIDER", "openai")
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "sk-test-key")
    remote = llm.build_chat_model("deepseek-flash")

    assert local is not remote


def test_none_model_falls_back_to_provider_default(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "local")
    monkeypatch.setattr(llm, "DEFAULT_MODEL", "fallback-model")
    # None resolves to DEFAULT_MODEL, so the implicit and explicit builds share a cache key.
    assert llm.build_chat_model() is llm.build_chat_model("fallback-model")
