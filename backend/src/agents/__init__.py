"""Agent building-block layer (src.agents).

Rol: reusable, composable "agent units" plus framework demo agents that show how
to build them.

Layout
------
- ``base.py``    : optional helpers/contracts for uniform agent units.
- ``samples/``   : official demo agents (localAgent/tsAgent/reflectAgent), meant
                   to be copied/adapted by users; they are *not* imported here so
                   that importing the agents package stays free of heavy side
                   effects (they pull the shared LLM only when the graph loads).

Shared, cross-domain capabilities are NOT defined here (they live in
``src.capabilities``) so agents and workflow lines never duplicate them.
"""

from __future__ import annotations

from . import base

__all__ = ["base"]
