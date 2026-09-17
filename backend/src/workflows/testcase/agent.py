"""Test-case generation workflow (demo business line).

Shows the intended assembly pattern for a purpose-built delivery:

    core.build_chat_model()          # framework kernel LLM
    capabilities.tools([...])        # shared, canonical tools
    capabilities.skills([...])       # expert guidance injected into system prompt
    src.agents building blocks       # (re)composed as needed

The compiled ``testcase_agent`` object is registered in ``agentConfig.yaml`` and
exposed by the API server just like any LangGraph graph.

It MUST be a real module-level attribute: ``langgraph_api`` resolves a registered
graph with ``module.__dict__[spec.variable]``, which never triggers PEP 562
``__getattr__`` — a lazy-only export would make the server fail at startup with
"Could not find graph 'testcase_agent'". Building it at import is cheap and
network-free (the model comes from the memoized ``src.core.llm`` factory).
"""

from __future__ import annotations

from src.capabilities.skills import get_texts
from src.capabilities.tools import builtin


def _system_prompt() -> str:
    """Build a scenario-specific system prompt from framework assets."""
    parts = [
        "You are a software testing analyst. Given a concise feature description ",
        "you produce a numbered, concrete set of test cases with: scenario title, "
        "precondition, action steps, expected result, and a priority (P0/P1/P2).",
        "",
        "You may use the shared tools when the scenario needs them.",
        "",
        # Inject the review skill as steerable policy (front-matter already stripped).
        "Review policy you must follow before your final answer:",
        *get_texts(["review_policy"]),
    ]
    return "\n".join(parts)


# Shared canonical tools (have a stable key name even if domain does not use them all).
def _tools():
    # add 'weather'/'current_date' so the agent visibly exercises shared registry
    return builtin(["weather", "current_date"])


def _build_agent():
    """Import heavy providers and compile the workflow agent (called once)."""
    from langchain.agents import create_agent

    from src.core.llm import build_chat_model

    return create_agent(
        model=build_chat_model(),
        tools=_tools(),
        system_prompt=_system_prompt(),
    )


# Real module-level attribute — langgraph_api reads registered graphs from
# `module.__dict__` (see module docstring), so a PEP 562 lazy export is invisible.
testcase_agent = _build_agent()


__all__ = ["testcase_agent"]
