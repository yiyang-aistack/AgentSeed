"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

A second, lightweight travel-support style agent (multi-agent demo).

Migrated from ``src/agents/tsAgent.py`` into ``agents/samples`` during the
framework restructure. It demonstrates two independent ``create_agent`` samples
that share the same memoized model and the canonical capability registry.

Before: diverging local tool definitions; after: both agents pull ``builtin``
tools from ``src.capabilities.tools`` — one source of truth.

Importing this module has no *network* side effects (it never calls Ollama or any
API). The compiled agent is exported as a **real module-level attribute** because
``langgraph_api`` resolves registered graphs with
``module.__dict__[spec.variable]`` — a PEP 562 ``__getattr__`` lazy export is
invisible to it and makes the server fail at startup.
"""

from __future__ import annotations

from src.capabilities.tools import builtin


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import)."""
    from langchain.agents import create_agent

    from src.core.llm import build_chat_model

    # A second, independent agent that shares the same memoized model instance.
    return create_agent(
        model=build_chat_model(),
        tools=builtin(["weather", "current_date"]),
        system_prompt=(
            "You are a friendly travel assistant. Help with weather and date questions, "
            "and answer general questions about trips."
        ),
    )


# Real module-level attribute — see the module docstring for why this cannot be lazy.
ts_agent = _build_agent()


__all__ = ["ts_agent"]
