"""Framework demo agents (sample/parade agents).

These illustrate different ways to build an agent on top of the framework:

- ``localAgent``  : single-shot ``create_agent`` bound to shared tools.
- ``tsAgent``     : a second lightweight ``create_agent`` example (multi-agent setup).
- ``reflectAgent``: hand-built StateGraph with a review/revise cycle.
- ``hermesAgent`` : ``create_agent`` whose "model" is a running Hermes Agent over HTTP.

They are meant to be copy-adapted by users; the real "reusable building blocks"
and patterns live in ``src.agents`` (see ``base.py``) + ``src.capabilities``.
"""

from __future__ import annotations

__all__: list[str] = []
