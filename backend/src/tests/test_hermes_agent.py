"""Tests for :mod:`src.agents.samples.hermesAgent` — configuration validation.

hermesAgent validates its required config at import time; the values are
injected by ``conftest.py`` before this module is imported.
"""

import pytest
from src.agents.samples import hermesAgent


def test_require_raises_when_variable_missing():
    with pytest.raises(RuntimeError, match="NOT_A_REAL_VAR is not set"):
        hermesAgent._require("NOT_A_REAL_VAR")


def test_require_returns_stripped_value():
    assert hermesAgent._require("HERMES_MODEL") == "hermes-agent"


def test_require_float_rejects_non_numeric(monkeypatch):
    monkeypatch.setenv("HERMES_TIMEOUT", "abc")
    with pytest.raises(RuntimeError, match="is not a number"):
        hermesAgent._require_float("HERMES_TIMEOUT")
