"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

Hermes-backed agent — the thing on the other end is an AGENT, not an LLM.

``localAgent`` binds a chat model and lets ``create_agent`` run the tool loop in
this process. This sample inverts that: `Hermes Agent
<https://github.com/NousResearch/hermes-agent>`_ runs its own agent loop (tools,
skills, memory, sessions) and exposes it over an OpenAI-compatible HTTP API, so
AgentSeed can publish a local Hermes instance as one more LangGraph graph
(``hermes_agent`` in ``agentConfig.yaml``) without configuring any LLM here.

Wire protocol (verified against Hermes Agent 0.20.6); every address below is the
``HERMES_BASE_URL`` configured in ``.env``::

    GET  <HERMES_BASE_URL>/health               platform / version probe
    GET  <HERMES_BASE_URL>/v1/models            -> {"id": "hermes-agent", ...}
    POST <HERMES_BASE_URL>/v1/chat/completions  OpenAI Chat Completions
                                                (SSE when "stream": true)
    Authorization: Bearer $API_SERVER_KEY       required on every route
    X-Hermes-Session-Id / X-Hermes-Session-Key  optional session headers

Two deliberate differences from ``localAgent``:

1. **No tools.** Hermes ignores a caller-supplied ``tools`` array and uses its
   own toolset/skills, so binding ``src.capabilities.tools`` here would only
   advertise tools that nobody calls. Tools stay where the agent loop lives.
2. **No ``src.core.llm``.** That factory builds *chat models* for Ollama or an
   OpenAI-compatible LLM endpoint; this graph must reach an agent runtime, so it
   owns a small, memoized client instead. Construction is deferred to graph
   build time, and importing this module never touches the network.

Configuration lives **only** in ``<repo>/.env`` (documented in ``.env.example``)
— no host, token, model id or timeout is hardcoded in this file — and is read
once, at import, with no side effects:

- required: ``HERMES_BASE_URL``, ``API_SERVER_KEY`` (the same variable name
  Hermes uses on its own side, so one value serves both), ``HERMES_MODEL`` and
  ``HERMES_TIMEOUT`` (seconds for one turn — an absent timeout means "wait
  forever" in the OpenAI-compatible client, so it may not be left implicit);
- optional: ``HERMES_MAX_RETRIES`` (empty = the client's own default) plus
  ``HERMES_SESSION_ID`` / ``HERMES_SESSION_KEY`` / ``HERMES_SYSTEM_PROMPT``.

A missing required variable fails at import with a message naming it and
pointing at ``.env`` / ``.env.example``, so ``.env`` stays the single source of
truth instead of silently falling back to a guess.

The compiled agent is exported as a **real module-level attribute** ``hermes``:
``langgraph_api`` resolves a registered graph with
``module.__dict__[spec.variable]`` and never triggers a PEP 562 ``__getattr__``,
so a lazy-only export would make the server fail with "Could not find graph".
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr

# ---------------------------------------------------------------------------
# Configuration — every value comes from <repo>/.env (see .env.example)
# ---------------------------------------------------------------------------

# Protocol constants of the Hermes API server. These are part of its wire
# contract (not user-tunable configuration): the OpenAI-compatible surface lives
# under this path, and these request headers carry the optional session scope.
_API_PATH = "/v1"
_SESSION_ID_HEADER = "X-Hermes-Session-Id"
_SESSION_KEY_HEADER = "X-Hermes-Session-Key"


def _env(name: str) -> str:
    """Return the stripped value of env var ``name`` (``""`` when unset/blank)."""
    return (os.getenv(name) or "").strip()


def _require(name: str) -> str:
    """Return a mandatory setting, failing loudly when ``.env`` lacks it.

    Failing here (instead of falling back to a magic value in this module) keeps
    ``.env`` the single source of truth: a wrong host or token must be fixed in
    ``.env``, never in the code.
    """
    value = _env(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. All Hermes settings live in <repo>/.env — see "
            f".env.example — so add `{name}=...` there. To run AgentSeed "
            "without Hermes, remove the hermes_agent entry from agentConfig.yaml."
        )
    return value


def _require_float(name: str) -> float:
    """Return a mandatory numeric setting (``.env`` supplies it)."""
    raw = _require(name)
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"{name}={raw!r} is not a number. Fix it in <repo>/.env — see .env.example."
        ) from exc


def _optional_int(name: str) -> int | None:
    """Return an optional integer setting, or ``None`` when unset/not numeric.

    ``None`` means "not configured": the caller then leaves the parameter out, so
    the OpenAI-compatible client keeps its own default instead of inheriting a
    magic number from this module.
    """
    raw = _env(name)
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


# --- required (no fallback: .env decides) ----------------------------------
# Root of the Hermes API server, e.g. http://127.0.0.1:8642 — Hermes' own
# default binding is API_SERVER_HOST=127.0.0.1 / API_SERVER_PORT=8642. Its
# OpenAI-compatible surface is derived by _chat_base_url() below.
HERMES_BASE_URL = _require("HERMES_BASE_URL").rstrip("/")

# Bearer token of that API server. The variable name is deliberately identical
# to Hermes' own (API_SERVER_KEY) so one value in .env serves both sides.
HERMES_API_KEY = _require("API_SERVER_KEY")

# Model id Hermes advertises on /v1/models (its API_SERVER_MODEL_NAME).
HERMES_MODEL = _require("HERMES_MODEL")

# Seconds to wait for one Hermes turn. Required rather than optional on purpose:
# the OpenAI-compatible client turns an absent timeout into httpx's
# Timeout(None) — "wait forever" — so the ceiling must be stated in .env instead
# of silently disappearing when the line is missing.
HERMES_TIMEOUT = _require_float("HERMES_TIMEOUT")

# --- optional (empty .env value = keep the client's own default) -----------
# HTTP retry ceiling: every retry re-runs the whole remote agent (tool calls
# included), so this knob belongs to .env rather than to this module.
HERMES_MAX_RETRIES = _optional_int("HERMES_MAX_RETRIES")

# Opt-in session continuity (`/v1/chat/completions` is stateless in Hermes) and
# bridge-level instructions. Empty = send nothing — see _session_headers().
HERMES_SESSION_ID = _env("HERMES_SESSION_ID")
HERMES_SESSION_KEY = _env("HERMES_SESSION_KEY")
HERMES_SYSTEM_PROMPT = _env("HERMES_SYSTEM_PROMPT")

# Built clients, keyed by model id: every caller that asks for the same Hermes
# model shares one instance (same idea as the memoized models in src.core.llm).
_instances: dict[str, BaseChatModel] = {}


def _chat_base_url() -> str:
    """OpenAI-compatible base URL: the configured root plus ``_API_PATH``.

    Tolerates a value that already carries the path, so both ``host:port`` and
    ``host:port/v1`` — the two forms people copy from client docs — work.
    """
    root = HERMES_BASE_URL
    if root.endswith(_API_PATH):
        root = root[: -len(_API_PATH)]
    return f"{root}{_API_PATH}"


def _session_headers() -> dict[str, str] | None:
    """Build the optional Hermes session headers (``None`` when none is set).

    They are HTTP headers, not body fields: Hermes reads them off the request,
    which is why they are passed as ``default_headers`` instead of model kwargs.
    """
    headers: dict[str, str] = {}
    if HERMES_SESSION_ID:
        headers[_SESSION_ID_HEADER] = HERMES_SESSION_ID
    if HERMES_SESSION_KEY:
        headers[_SESSION_KEY_HEADER] = HERMES_SESSION_KEY
    return headers or None


def build_hermes_chat_model() -> BaseChatModel:
    """Build (or return a cached) OpenAI-compatible client for Hermes.

    Hermes speaks the OpenAI wire format, so ``ChatOpenAI`` is all that is
    needed; the "model" it selects is the remote agent itself (``HERMES_MODEL``).
    Sampling (temperature / top_p) is never sent — that is the business of the
    agent runtime which actually runs the turn, not of this bridge.

    Returns:
        A :class:`ChatOpenAI` pointed at the configured OpenAI-compatible URL.

    Raises:
        ImportError: If ``langchain-openai`` (the OpenAI-compatible client) is
            not installed.
    """
    cached = _instances.get(HERMES_MODEL)
    if cached is not None:
        return cached

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - only without the dependency
        raise ImportError(
            "langchain-openai is not installed, but agents.samples.hermesAgent "
            "uses it as the OpenAI-compatible client for the Hermes API server. "
            "Add it to pyproject.toml and re-run `uv sync`."
        ) from exc

    # Only the optional knobs go through this bag: an empty .env value must leave
    # the client's own default in place (see HERMES_TIMEOUT for why the timeout
    # itself is required instead).
    optional: dict[str, Any] = {}
    if HERMES_MAX_RETRIES is not None:
        optional["max_retries"] = HERMES_MAX_RETRIES

    model = ChatOpenAI(
        model=HERMES_MODEL,
        # SecretStr matches the declared field type and keeps the token out of
        # reprs / logs.
        api_key=SecretStr(HERMES_API_KEY),
        base_url=_chat_base_url(),
        timeout=HERMES_TIMEOUT,
        # X-Hermes-Session-* are request headers, not body fields.
        default_headers=_session_headers(),
        # `streaming` is left at the LangChain default: ChatOpenAI switches to
        # SSE when the caller streams, and since Hermes implements
        # "stream": true the frontend gets token-by-token output for free.
        **optional,
    )
    _instances[HERMES_MODEL] = model
    return model


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import).

    Building the graph at import is what ``langgraph_api`` requires, and it
    stays network-free: ``ChatOpenAI`` only stores its configuration, the first
    HTTP request happens when the graph is actually invoked.
    """
    from langchain.agents import create_agent

    return create_agent(
        model=build_hermes_chat_model(),
        # Empty on purpose — see the module docstring: Hermes owns the tools.
        tools=[],
        system_prompt=HERMES_SYSTEM_PROMPT or None,
    )


# Real module-level attribute — langgraph_api reads registered graphs from
# `module.__dict__` (see the module docstring for why a lazy export fails).
hermes = _build_agent()


__all__ = ["hermes"]
