"""MCP server lifecycle manager (framework kernel).

Responsibilities:
--------------------
- Read connection parameters from declarative ``servers.yaml``;
- Manage connection lifecycle, avoiding memory leaks and duplicate connections.
- Convert server tools to ``BaseTool`` list to return to agent.

The adapter behind this is ``langchain-mcp-adapters`` (declared in
``pyproject.toml``); it ships ``mcp`` with it. ``stdio`` and
``streamable-http`` / ``sse`` are both supported — the transport string in
``servers.yaml`` is translated by :data:`_TRANSPORT_ALIASES`.

Why this module is synchronous
------------------------------
Agent modules are imported by ``langgraph_api`` at startup and must publish a
**real module-level attribute**, so tool resolution has to finish *during*
import — while the MCP client is async-only. :func:`_run_sync` bridges the two
by running the coroutine on a private event loop in a worker thread, which works
both when the import happens outside a loop and when it happens inside a running
one (a bare ``asyncio.run`` would raise there).

The tools this returns are **self-connecting**: ``langchain-mcp-adapters`` opens
a fresh session per tool call, so nothing here holds a live socket open between
calls and there is no idle connection to leak. What is cached is the client
(config only), not a session.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentseed.capabilities.mcp")

# ``${VAR}`` placeholders inside servers.yaml resolve against the process
# environment — which backend/main.py has already filled from <repo>/.env, so
# .env stays the single source of truth and no key is ever written into YAML.
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# servers.yaml spells transports the way the MCP documentation does; the adapter
# accepts several spellings, but normalising here keeps error messages and tests
# unambiguous.
_TRANSPORT_ALIASES = {
    "stdio": "stdio",
    "sse": "sse",
    "websocket": "websocket",
    "http": "streamable_http",
    "streamable_http": "streamable_http",
    "streamable-http": "streamable_http",
}

# Keys kept when handing a spec to the adapter. Everything else in servers.yaml
# is framework-level metadata (``enabled``) and would otherwise be splatted into
# the session constructor as an unexpected kwarg.
_CONNECTION_KEYS = (
    "transport",
    "url",
    "headers",
    "command",
    "args",
    "env",
    "cwd",
    "timeout",
    "sse_read_timeout",
    "terminate_on_close",
    "session_kwargs",
    "auth",
)


class MCPConfigError(RuntimeError):
    """A declared MCP server is unusable (no key, bad transport, missing url…).

    Raised *before* any network I/O, so callers can distinguish "this server was
    never configured" from "this server was configured but is unreachable" — the
    two want different advice.
    """


def _expand_env(value: Any, missing: set[str]) -> Any:
    """Recursively expand ``${VAR}`` placeholders in a parsed YAML value.

    Args:
        value: Any YAML fragment (str / dict / list / scalar).
        missing: Output set; every placeholder that resolved to empty is recorded
            here, so the caller can name the exact variable in its error instead
            of leaving a silently empty header.

    Returns:
        The fragment with placeholders substituted (missing ones become ``""``).
    """

    if isinstance(value, str):

        def _substitute(match: re.Match[str]) -> str:
            name = match.group(1)
            raw = os.getenv(name, "")
            if not raw.strip():
                missing.add(name)
            return raw

        return _ENV_PATTERN.sub(_substitute, value)
    if isinstance(value, dict):
        return {key: _expand_env(item, missing) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item, missing) for item in value]
    return value


def _run_sync(coro: Any) -> Any:
    """Run ``coro`` to completion on a private event loop and return its result.

    A worker thread is used rather than ``asyncio.run`` because graph modules are
    imported by ``langgraph_api``, and that import may already be inside a running
    loop — exactly where ``asyncio.run`` raises "cannot be called from a running
    event loop". The whole coroutine runs inside the worker's loop, so no asyncio
    object ever crosses between loops.

    Exceptions are re-raised in the calling thread with their original type, so
    callers see the adapter's own errors (e.g. connection refused) unchanged.
    """
    outcome: dict[str, Any] = {}

    def _target() -> None:
        try:
            outcome["value"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller
            outcome["error"] = exc

    worker = threading.Thread(target=_target, name="agentseed-mcp", daemon=True)
    worker.start()
    worker.join()

    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


class _Manager:
    """Lifecycle manager over the servers declared in ``servers.yaml``."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path(__file__).with_name("servers.yaml")
        self._sessions: dict[str, object] = {}

    # -- config ---------------------------------------------------------
    def _specs(self) -> dict:
        import yaml

        raw = yaml.safe_load(self._config_path.read_text(encoding="utf-8")) or {}
        return raw.get("servers", {}) or {}

    def spec(self, server: str) -> dict:
        """Return the declared spec for ``server`` with ``${VAR}`` expanded."""
        raw = self._specs().get(server)
        if not raw:
            raise KeyError(f"Unknown MCP server {server!r}.")
        return dict(_expand_env(raw, set()))

    # -- config -> adapter connection -----------------------------------
    def connection(self, server: str) -> dict:
        """Translate a declared spec into a ``langchain-mcp-adapters`` connection.

        Raises:
            MCPConfigError: If a required ``${VAR}`` is unset, the transport is
                unknown, or the fields that transport requires are absent. The
                message names the offending variable/field and points at the two
                files involved, so the fix needs no further digging.
        """
        missing: set[str] = set()
        spec = _expand_env(self._specs().get(server) or {}, missing)
        if not spec:
            raise KeyError(f"Unknown MCP server {server!r}.")

        if missing:
            raise MCPConfigError(
                f"MCP server {server!r} needs {', '.join(sorted(missing))}, which is "
                f"not set in <repo>/.env (see .env.example). Placeholders are expanded "
                f"by {Path(__file__).name} against the process environment."
            )

        transport = _TRANSPORT_ALIASES.get(str(spec.get("transport", "")).strip().lower())
        if not transport:
            raise MCPConfigError(
                f"MCP server {server!r} declares transport {spec.get('transport')!r}; "
                f"expected one of {', '.join(sorted(_TRANSPORT_ALIASES))}."
            )

        # Only known connection keys travel on: `enabled` and any future
        # framework-level metadata stay here.
        connection = {key: spec[key] for key in _CONNECTION_KEYS if key in spec}
        connection["transport"] = transport

        if transport == "stdio":
            for field in ("command", "args"):
                if not connection.get(field):
                    raise MCPConfigError(
                        f"MCP server {server!r} uses transport 'stdio' but declares no "
                        f"{field!r}; add it to {self._config_path.name}."
                    )
        elif not connection.get("url"):
            raise MCPConfigError(
                f"MCP server {server!r} uses transport {transport!r} but declares no "
                f"'url'; add it to {self._config_path.name}."
            )

        return connection

    # -- lifecycle ------------------------------------------------------
    def _open(self, server: str) -> object:
        """Build (and keep) the adapter client for ``server``.

        The client is config-only — it holds the connection parameters, not a
        live session — so caching it is enough to avoid rebuilding on every call.
        """
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError as exc:  # pragma: no cover - only without the dependency
            raise ImportError(
                "langchain-mcp-adapters is not installed, but the MCP capability "
                "layer needs it. Add it to pyproject.toml and re-run `uv sync`."
            ) from exc

        return MultiServerMCPClient({server: self.connection(server)})

    def _load_tools(self, session: object) -> list:
        """Convert a connected client into a list of ``BaseTool``.

        ``get_tools()`` lists the server's tools and returns wrappers that open a
        fresh session per call, so the tools stay valid after this returns.
        """
        return list(_run_sync(session.get_tools()))

    def connect_and_tools(self, server: str) -> list:
        """Connect (reuse if possible) and return the server's tool list."""
        if server not in self._sessions:
            logger.info(
                "Opening MCP server: %s (transport=%s)",
                server,
                self.connection(server).get("transport"),
            )
            self._sessions[server] = self._open(server)
        return self._load_tools(self._sessions[server])

    def shutdown(self) -> None:
        """Drop every cached client (the tools themselves need no teardown)."""
        self._sessions.clear()


_inst: _Manager | None = None


def manager() -> _Manager:
    global _inst
    if _inst is None:
        _inst = _Manager()
    return _inst


__all__ = ["manager", "_Manager", "MCPConfigError"]
