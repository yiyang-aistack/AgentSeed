"""Workflows — end-user business lines that *compose* framework building blocks.

What belongs here
-----------------
A workflow is a higher-level orchestration / delivery process for a concrete
product goal (e.g. "generate test cases", "run perf benchmarks"). It typically:
- pulls reusable pieces from ``src.agents``(agent components) + ``capabilities``
  (tools / mcp / skills) + ``core``(LLM factory / logging);
- adds scenario-specific prompts, parameters and state wiring.

It does NOT re-define generic agents or duplicate shared tools — reading the
"one concept one directory" rule, ``agents`` (reusable demos/components) and
``workflows`` (purpose-built deliveries) never overlap in naming/roles.

Guidance for new business lines
-------------------------------
Prefer a flat sub-package per line, e.g.::

    workflows/
      testcase/       agent.py, prompts.py, __init__ (exposes the compiled graph)
      performance/    ...

Each line exposes ONE "entry graph" object in its ``__init__`` so ``agentConfig.yaml``
can register it as an HTTP endpoint easily.
"""

from __future__ import annotations

__all__: list[str] = []
