"""MCP (Model Context Protocol) capability sub-layer.

External-capability integration: turns a configured MCP server into a list of
BaseTool objects that agents can bind, without agents knowing MCP details.

THIS LAYER IS LIVE FOR REMOTE AND LOCAL MCP SERVERS.
``langchain-mcp-adapters`` (and the ``mcp`` SDK it brings in) is a declared
dependency, so both transports are wired end to end:
- servers.yaml : declarative config (same style as agentConfig.yaml), per MCP server;
- manager.py   : server lifecycle, spec expansion and tool loading;
- tools()      : stable fetch interface — the only thing an agent imports.

Supported transports:
- stdio : command + args (the server runs as a subprocess)
- streamable-http / sse : url + optional headers (a remote endpoint)

Declaring a server is config-only; ``${VAR}`` placeholders in servers.yaml are
expanded from ``.env``, so no key is written into YAML. A missing placeholder
raises :class:`~src.capabilities.mcp.manager.MCPConfigError` **before** any
connection attempt, which lets a caller tell "never configured" apart from
"configured but unreachable".

Usage::

    from src.capabilities.mcp import tools
    tool_list = tools("tavily")   # -> list[BaseTool]
"""

from __future__ import annotations

from pathlib import Path

from . import manager as _manager


def _config_path() -> Path:
    return Path(__file__).with_name("servers.yaml")


def _enabled_server_names() -> list[str]:
    """Parse servers.yaml and return names of enabled servers (config-only)."""
    import yaml

    raw: dict = {}
    cfg = _config_path()
    if cfg.exists():
        raw = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    servers = raw.get("servers", {}) or {}
    return [name for name, spec in servers.items() if spec.get("enabled", False)]


def available_servers() -> list[str]:
    """Names of enabled MCP servers declared in servers.yaml."""
    return _enabled_server_names()


def tools(server: str | None = None) -> list:
    """Resolve tools for an enabled MCP server.

    Backed by Manager: lists the server's tools and returns them as ``BaseTool``
    objects. Each returned tool opens its own session when invoked, so the list
    can be bound to an agent and reused freely.

    Raises:
        ValueError: If ``server`` is omitted while several servers are enabled.
        KeyError: If ``server`` is not enabled in ``servers.yaml``.
        MCPConfigError: If the server is enabled but under-configured (unset env
            placeholder, unknown transport, missing url/command).
    """
    names = available_servers()
    if server is None:
        if len(names) != 1:
            raise ValueError(f"Specify a server name; enabled servers: {names}")
        server = names[0]
    if server not in names:
        raise KeyError(f"MCP server {server!r} not enabled in {_config_path()}.")
    return _manager.manager().connect_and_tools(server)


__all__ = ["tools", "available_servers"]
