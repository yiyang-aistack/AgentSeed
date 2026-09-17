"""Capability layer — frameworks to attach *cross-agent* abilities.

This is name space of this framework for usable capabilities or assets.

- tools   : local function tools declared as ``@tool``.
- mcp     : external stdio / streamable-http MCP server tools.
- skills  : prompt/skill text assets.

Why not put in src.agents
-------------------------------
Ability to be shared across multiple agent / workflow, if it is private to one agent, it will cause
"agent"/"ability" semantic confusion and potential circular dependencies.
Thus, it is moved to the same level as ``src.agents``.

Usage
------------------
>>> from src.capabilities import capabilities
>>> tools  = capabilities.tools(["weather", "current_date"])
>>> mcp    = capabilities.mcp("filesystem")          # if enables server - filesystems or sandbox
>>> prompts = capabilities.skills(["review_policy"]) # get skill text assets
"""

from __future__ import annotations

from . import mcp as _mcp
from . import skills as _skills
from . import tools as _tools


class _Capabilities:
    """Convenience facade aggregating the three sub-layers (single call site)."""

    def tools(self, names: list[str] | None = None) -> list:
        """Return built-in local tools, optionally filtered by name. See .tools."""
        return _tools.builtin(names)

    @staticmethod
    def mcp(server: str) -> list:
        """Build BaseTool list from an enabled MCP server name (see .mcp registry)."""
        return _mcp.tools(server)

    @staticmethod
    def skills(names: list[str] | None = None) -> list[str]:
        """Return skill text blobs by name (see .skills loader)."""
        return _skills.get_texts(names)


capabilities = _Capabilities()

__all__ = [
    "capabilities",
    "_tools",
    "_mcp",
    "_skills",
]
