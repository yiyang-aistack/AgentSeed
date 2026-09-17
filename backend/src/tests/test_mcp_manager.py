"""Tests for :mod:`src.capabilities.mcp.manager` — spec parsing and validation.

Everything here is offline: these are the checks that run *before* the manager is
allowed to open a connection, which is what lets an agent tell "never configured"
apart from "configured but unreachable". Each test builds its own ``servers.yaml``
in ``tmp_path`` so the shipped file stays the source of truth for the real graph.
"""

import textwrap

import pytest
from src.capabilities.mcp.manager import MCPConfigError, _Manager


def _manager(tmp_path, body: str) -> _Manager:
    """Write ``body`` as a servers.yaml and return a manager bound to it."""
    config = tmp_path / "servers.yaml"
    config.write_text(textwrap.dedent(body), encoding="utf-8")
    return _Manager(config_path=config)


def test_spec_expands_env_placeholder(tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-secret")
    mgr = _manager(
        tmp_path,
        """
        servers:
          tavily:
            transport: streamable-http
            url: https://mcp.tavily.com/mcp/
            headers:
              Authorization: "Bearer ${TAVILY_API_KEY}"
        """,
    )
    assert mgr.spec("tavily")["headers"]["Authorization"] == "Bearer tvly-secret"


def test_missing_placeholder_raises_before_connecting(tmp_path, monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    mgr = _manager(
        tmp_path,
        """
        servers:
          tavily:
            transport: streamable-http
            url: https://mcp.tavily.com/mcp/
            headers:
              Authorization: "Bearer ${TAVILY_API_KEY}"
        """,
    )
    with pytest.raises(MCPConfigError, match="TAVILY_API_KEY"):
        mgr.connection("tavily")


def test_blank_placeholder_counts_as_missing(tmp_path, monkeypatch):
    """An ``.env`` line left empty must not silently produce `Bearer `."""
    monkeypatch.setenv("TAVILY_API_KEY", "   ")
    mgr = _manager(
        tmp_path,
        """
        servers:
          tavily:
            transport: streamable-http
            url: https://mcp.tavily.com/mcp/
            headers:
              Authorization: "Bearer ${TAVILY_API_KEY}"
        """,
    )
    with pytest.raises(MCPConfigError, match="TAVILY_API_KEY"):
        mgr.connection("tavily")


def test_connection_strips_framework_metadata(tmp_path):
    """``enabled`` is ours, not the adapter's — it must not reach the session."""
    mgr = _manager(
        tmp_path,
        """
        servers:
          tavily:
            transport: streamable-http
            url: https://mcp.tavily.com/mcp/
            enabled: true
        """,
    )
    connection = mgr.connection("tavily")
    assert connection == {"transport": "streamable_http", "url": "https://mcp.tavily.com/mcp/"}


def test_transport_spelling_is_normalised(tmp_path):
    """servers.yaml uses the docs' ``streamable-http``; the adapter wants snake_case."""
    mgr = _manager(
        tmp_path,
        """
        servers:
          remote:
            transport: streamable-http
            url: https://example.test/mcp
        """,
    )
    assert mgr.connection("remote")["transport"] == "streamable_http"


def test_unknown_transport_is_rejected(tmp_path):
    mgr = _manager(
        tmp_path,
        """
        servers:
          broken:
            transport: carrier-pigeon
            url: https://example.test/mcp
        """,
    )
    with pytest.raises(MCPConfigError, match="carrier-pigeon"):
        mgr.connection("broken")


def test_remote_transport_requires_url(tmp_path):
    mgr = _manager(
        tmp_path,
        """
        servers:
          broken:
            transport: streamable-http
        """,
    )
    with pytest.raises(MCPConfigError, match="url"):
        mgr.connection("broken")


def test_stdio_requires_command_and_args(tmp_path):
    mgr = _manager(
        tmp_path,
        """
        servers:
          broken:
            transport: stdio
        """,
    )
    with pytest.raises(MCPConfigError, match="command"):
        mgr.connection("broken")


def test_stdio_connection_is_passed_through(tmp_path):
    mgr = _manager(
        tmp_path,
        """
        servers:
          filesystem:
            transport: stdio
            command: npx
            args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/scratch"]
        """,
    )
    connection = mgr.connection("filesystem")
    assert connection["command"] == "npx"
    assert connection["args"][-1] == "/tmp/scratch"


def test_unknown_server_raises_key_error(tmp_path):
    mgr = _manager(tmp_path, "servers: {}")
    with pytest.raises(KeyError, match="Unknown MCP server"):
        mgr.spec("nope")
