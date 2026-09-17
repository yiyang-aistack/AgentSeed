"""Tests for :mod:`src.capabilities.tools.registry` — the name→tool resolver."""

import pytest
from src.capabilities.tools import registry


def test_resolve_returns_all_builtins_when_none():
    tools = registry.resolve()
    assert len(tools) == len(registry._BUILTINS)


def test_resolve_returns_known_tool_by_logical_key():
    [tool_] = registry.resolve(["weather"])
    assert tool_ is registry.get_weather


def test_resolve_returns_tool_by_function_name_alias():
    [tool_] = registry.resolve(["get_current_date"])
    assert tool_ is registry.get_current_date


def test_resolve_unknown_name_raises_key_error():
    with pytest.raises(KeyError, match="No built-in tool named 'nope'"):
        registry.resolve(["nope"])
