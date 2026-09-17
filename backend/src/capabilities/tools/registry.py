"""In-process tool registry.

The framework-level "loader" that turns named tools into actual
``langchain_core.tools.BaseTool`` objects shared across agents/workflows.

Design mirrors the ``src.core.llm`` philosophy: a single, canonical source of
truth + lazy resolution, so no agent hard-codes and duplicates tool definitions.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

# ---------------------------------------------------------------------------
# Built-in, domain-agnostic tools (process-local functions)
# ---------------------------------------------------------------------------


@tool
def get_weather(city: str) -> str:
    """Get the (mock) current weather for a given city.

    Deterministic stub so agents can run offline; swap the body for a real weather
    API (e.g. OpenWeatherMap) when wired to production.
    """
    return f"It's always sunny in {city}."


@tool
def get_current_date() -> str:
    """Get today's local date (YYYY-MM-DD). Useful for date-aware prompts."""
    from datetime import date

    return date.today().isoformat()


# Registry key -> callable that returns a BaseTool.
# Keeping a name → tool map here lets agents pull exactly what they need by name.
# NOTE: ``BUILTINS`` (public alias below) is the read-only registry facade;
# consumers should prefer ``resolve()`` / the ``__all__`` exports over mutating it.
_BUILTINS: dict[str, BaseTool] = {
    # NOTE: use the func's __name__ as stable logical key.
    "weather": get_weather,
    "current_date": get_current_date,
}
# Also register aliasing by the decorated function's own name for convenience.
_BUILTINS.setdefault(get_weather.name, get_weather)
_BUILTINS.setdefault(get_current_date.name, get_current_date)

# Public read-only view — keep the underscored storage private so callers do
# not casually mutate the shared registry (see module docstring / review policy).
# NOTE: this is a *snapshot taken at import time*. Registering a tool later
# (``_BUILTINS["x"] = ...``) does NOT update it, so always fetch tools through
# ``resolve()`` / ``builtin()`` if you need late registrations to be visible.
BUILTINS: dict[str, BaseTool] = dict(_BUILTINS)


def resolve(names: list[str] | None = None) -> list[BaseTool]:
    """Return the requested built-in tools by key (default: all built-ins)."""
    if names is None:
        return list(_BUILTINS.values())
    resolved: list[BaseTool] = []
    for name in names:
        try:
            resolved.append(_BUILTINS[name])
        except KeyError:
            raise KeyError(
                f"No built-in tool named {name!r}. Available: {sorted(_BUILTINS)}"
            ) from None
    return resolved


__all__ = ["get_weather", "get_current_date", "resolve", "BUILTINS"]
