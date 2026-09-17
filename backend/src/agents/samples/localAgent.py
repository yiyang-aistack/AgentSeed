"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

Sample single-shot agent: a tool-calling agent backed by the shared LLM.

Migrated here from the repo-root ``localAgent.py`` as part of the framework
restructure (``agents/samples`` = demo units). It mirrors what the framework
expects any agent unit to look like and keeps the module pattern consistent with
``tsAgent`` / ``reflectAgent``:

- model construction deferred to the shared, memoized ``src.core.llm`` factory;
- tools come from the canonical registry ``src.capabilities.tools``;
- the compiled agent is exported as a **real module-level attribute**
  ``test_agent``. This is required by ``langgraph_api``, which resolves a
  registered graph with ``module.__dict__[spec.variable]`` and therefore cannot
  see PEP 562 ``__getattr__``-only (lazy) exports. Building it here is still
  side-effect-free in the network sense: it only constructs a chat-model object
  through the memoized factory (no API call, no server access).
"""

from __future__ import annotations

from src.capabilities.tools import builtin


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import)."""
    from langchain.agents import create_agent

    from src.core.llm import build_chat_model

    # Single, shared chat model — cached by the factory in src.core.llm.
    return create_agent(
        model=build_chat_model(),
        tools=builtin(["weather", "current_date"]),
        system_prompt=(
            "You are a helpful assistant. Use the provided tools when the user "
            "asks about the weather or needs today's date."
        ),
    )


# Must be a REAL module-level attribute: langgraph_api resolves a registered
# graph via `module.__dict__[spec.variable]`, which never triggers PEP 562
# `__getattr__`. A lazy-only export makes the server die at startup with
# "Could not find graph 'test_agent'".
test_agent = _build_agent()


__all__ = ["test_agent"]
