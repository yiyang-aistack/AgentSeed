"""Reusable agent building-block helpers (framework layer).

``src.agents`` is the library of *reusable, composable* agent units. Individual
agents may be as simple as a ``create_agent`` result or a hand-built StateGraph.

This module provides optional helpers that make the "building block" contract
explicit and uniform across many agents — without forcing every agent to inherit.
The key idea: an agent unit should expose, at minimum:

- ``graph``    : the compiled runnable (LangGraph CompiledStateGraph / Runnable);
- ``name``     : stable id for logging / registry;
- ``meta``     : dict describing inputs/outputs/tools (frameworks/tools introspection).

These attributes are *conventions*, asserted by ``assert_agent_ready`` for the
frameworks that want to validate all registered units.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("agentseed.agents.base")


@dataclass
class AgentMeta:
    """Descriptor an agent unit may carry, used by registry/tooling UX.

    Reserved contract: nothing in this repository constructs or consumes it yet
    (the sample agents build their graphs directly), so treat the shape as a
    forward-looking convention rather than an enforced one.
    """

    name: str
    description: str = ""
    tools_used: list[str] = field(default_factory=list)
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)


def assert_agent_ready(graph: Any, *, name: str) -> None:
    """Lightweight sanity guard for a candidate agent unit.

    Reserved contract: no call site exists in this repository yet; wire it into
    your own registry/CLI when you want these checks enforced.

    Args:
        graph: should be a compiled LangGraph/Runnable (has ``invoke`` / ``stream``).
        name: logical name used in error messages.
    """
    if graph is None:
        raise ValueError(f"Agent {name!r} has no graph (None).")
    for attr in ("invoke", "stream"):
        if not hasattr(graph, attr):
            logger.debug("Agent %s lacks %r (may be fine for pure function).", name, attr)


__all__ = ["AgentMeta", "assert_agent_ready"]
