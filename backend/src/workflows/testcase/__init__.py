"""Test-case generation workflow(demo business line).

Shows the intended assembly pattern for a purpose-built delivery:

    core.build_chat_model()          # framework kernel LLM
    capabilities.tools([...])        # shared, canonical tools
    capabilities.skills([...])       # expert guidance injected into system prompt
    src.agents building blocks       # (re)composed as needed

The compiled ``testcase_agent`` object is registered in ``agentConfig.yaml`` and
exposed by the API server just like any LangGraph graph.

It is re-exported **eagerly** (and therefore lives in this module's ``__dict__``),
because ``langgraph_api`` resolves a registered graph with
``module.__dict__[spec.variable]`` and never triggers PEP 562 ``__getattr__``.
The heavy lifting still happens in the memoized model factory
(``src.core.llm.build_chat_model``), which performs no network I/O.
"""

from __future__ import annotations

from .agent import testcase_agent

__all__ = ["testcase_agent"]
