"""Built-in(native/process-local) function tools registry.

declare tools as ``@tool`` and aggregate them in a retrievable registry, avoid duplication of
old ``src.agents.tools``

Usage
----
>>> from src.capabilities.tools import builtin
>>> tools = builtin(["weather", "current_date"])

>> If no names are provided, return all tools in registry.
"""

from __future__ import annotations

from . import registry as _registry


def builtin(names: list[str] | None = None) -> list:
    """Return requested built-in tools by their registry keys.

    Args:
        names: list of tool keys (e.g. ``["weather", "current_date"]``). If ``None``,
            all built-in tools are returned.

    Returns:
        List of ``langchain_core.tools.BaseTool`` instances.

    Raises:
        KeyError: If a requested name is not a registered built-in.
    """
    return _registry.resolve(names)


__all__ = ["builtin"]
