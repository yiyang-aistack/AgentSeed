"""Discovery/parsing for skill assets.

Supported asset kinds in ``entries/``:
1. ``<name>.md``  with optional YAML front matter (---\\n key: val \\n ---).
2. ``<name>.py``  exporting ``SKILL_TEXT: str`` and optional ``SKILL_META: dict``.

A small cache avoids re-reading text assets per call.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_ENTRIES_DIR = Path(__file__).with_name("entries")

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _discover_md() -> dict[str, Path]:
    if not _ENTRIES_DIR.exists():
        return {}
    return {p.stem: p for p in _ENTRIES_DIR.glob("*.md")}


def _discover_py() -> dict[str, Path]:
    if not _ENTRIES_DIR.exists():
        return {}
    return {p.stem: p for p in _ENTRIES_DIR.glob("*.py") if not p.name.startswith("_")}


def discover() -> list[str]:
    return sorted(set(_discover_md()) | set(_discover_py()))


def _load_md(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if _FRONT_MATTER_RE.match(text):
        return _FRONT_MATTER_RE.sub("", text).strip()
    return text.strip()


def _load_py(path: Path) -> str:
    import importlib.util

    module_name = f"_skill_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load skill module {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return (getattr(mod, "SKILL_TEXT", "") or "").strip()


def _get_texts_uncached(names: tuple[str, ...] | None = None) -> list[str]:
    if names is None:
        names = tuple(discover())
    md = _discover_md()
    py = _discover_py()
    out: list[str] = []
    for name in names:
        if name in md:
            out.append(_load_md(md[name]))
        elif name in py:
            out.append(_load_py(py[name]))
        else:
            raise KeyError(f"No skill named {name!r}. Available: {discover()}")
    return out


def get_texts(names: list[str] | None = None) -> list[str]:
    """Return requested skill body texts (front-matter stripped). Cacheable."""
    key = None if names is None else tuple(names)
    return _get_texts_cached(key)


_get_texts_cached = lru_cache(maxsize=64)(_get_texts_uncached)  # type: ignore[assignment]


__all__ = ["discover", "get_texts"]
