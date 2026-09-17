"""Skills — prompt/knowledge assets that steer agent behavior.

A Skill is *mostly prompting*, not executable code: it packages expert guidance,
rules, or a playbook as text. Optionally it can reference the names of tools it
builds on, letting the loader tell agents which tools to bind.

Skill asset locations (this package scans the ``entries/`` folder):
- markdown with ``---`` YAML front-matter (non-engineer friendly), OR
- plain ``.py`` modules exporting ``SKILL_TEXT`` / ``SKILL_META`` (programmable).

Design keeps skills cacheable and stable so repeated helps behave the same.

Example (markdown asset ``entries/review_policy.md``)::

    ---
    name: review_policy
    description: Code/agent output review guidance
    tools: []
    ---
    # Review policy
    Always prefer minimal, idempotent changes...

Use from code::

    from src.capabilities.skills import get_texts
    blobs = get_texts(["review_policy"])   # -> list[str] of body text (front-matter stripped)
"""

from __future__ import annotations

from . import loader as _loader


def get_texts(names: list[str] | None = None) -> list[str]:
    """Return requested skill body texts (YAML front-matter stripped)."""
    return _loader.get_texts(names)


def available() -> list[str]:
    """Names of skills found in the assets directory."""
    return _loader.discover()


__all__ = ["get_texts", "available"]

# The ``entries/`` folder holds actual skill assets (markdown or .py); it does
# not need to be imported as a module here — the loader scans it on demand.
