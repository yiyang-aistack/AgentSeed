"""Centralized, lazy LLM provider factory (single source of truth).

Why this exists
---------------
The previous design let each agent module build its own chat model directly at
*module import time*:

    # ❌ old localAgent.py style
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)   # import-time side effect

That caused several problems this module fixes:

1. Duplicated config & duplicated model instances across agents
   (every agent imported and constructed its own ``ChatOllama`` with slightly drifting env keys).
2. Eager import: ``from langchain_ollama import ChatOllama`` ran during ``import``,
   so a missing / slow package or unreachable Ollama could break *any* module import.
3. No single place to swap Ollama -> a hosted/OpenAI-compatible runtime later.

Design
------
- Reading configuration happens once, safely (`getenv`, no side effects).
- ``LLM_PROVIDER`` selects the backend: ``local`` (Ollama) or ``openai`` (any
  OpenAI-compatible endpoint: DeepSeek / qwen / glm/kimi ...). The provider package is
  imported lazily, so a missing/failed backend never breaks module import.
- The heavy work (`import <provider>`, constructing the client) is deferred to
  ``build_chat_model()`` and memoized, so all agents that need an LLM share ONE instance.
- Import errors are surfaced at *build* time (when an agent actually needs an LLM),
  not at module import — keeping unrelated modules importable.
"""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

# ---------------------------------------------------------------------------
# Configuration (read once, safe at import time)
# ---------------------------------------------------------------------------

_LLM_MODULE = "src.core.llm"

# Which backend builds the chat model:
#   "local"  -> local Ollama server (default: no API key, no network needed)
#   "openai" -> any OpenAI-compatible endpoint (DeepSeek / qwen2 / glm/kimi ...)
# Defaults to "local" so behaviour is unchanged when the switch is absent.
PROVIDER = (os.getenv("LLM_PROVIDER") or "local").strip().lower()

# Ollama endpoint / default model. .env is the single source of truth; these are
# only fallbacks so the factory works even if PORT/HOST style vars are unset.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# OpenAI-compatible endpoint — only used when PROVIDER == "openai".
# The fallback host stays on the OFFICIAL domain on purpose: a wrong host here
# would ship the API key + every prompt to a third party.
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-flash")

# Cache of already-built chat models, keyed by (provider, model name) so that
# switching provider cannot accidentally reuse the other backend's instance.
_instances: dict[tuple[str, str], BaseChatModel] = {}


def _temperature(var: str) -> float:
    """Read a temperature env var, falling back to 0.2 on empty/garbage input."""
    try:
        return float(os.getenv(var) or "0.2")
    except ValueError:
        return 0.2


def _build_ollama(model_name: str) -> BaseChatModel:
    """Build a local Ollama chat model (``LLM_PROVIDER=local``)."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:  # pragma: no cover - exercised only without the dep
        raise ImportError(
            "langchain-ollama is not installed. Add it to pyproject.toml and "
            "re-run `uv sync` before registering an LLM-backed agent. "
            f"(imported from {_LLM_MODULE})"
        ) from exc

    try:
        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=_temperature("OLLAMA_TEMPERATURE"),
        )
    except Exception as exc:  # e.g. bad URL / model name rejected at construction
        raise RuntimeError(
            f"Failed to build chat model {model_name!r} against {OLLAMA_BASE_URL!r}. "
            "Check that Ollama is running and the model is pulled."
        ) from exc


def _build_openai(model_name: str) -> BaseChatModel:
    """Build a model on any OpenAI-compatible endpoint (``LLM_PROVIDER=openai``)."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "LLM_PROVIDER=openai requires OPENAI_API_KEY, but it is empty. "
            "Set it in .env and keep the value on its own line (an inline `#` "
            "comment would be parsed as part of the key)."
        )

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - exercised only without the dep
        raise ImportError(
            "langchain-openai is not installed. Add it to pyproject.toml and "
            "re-run `uv sync` before setting LLM_PROVIDER=openai. "
            f"(imported from {_LLM_MODULE})"
        ) from exc

    try:
        return ChatOpenAI(
            model=model_name,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=_temperature("OPENAI_TEMPERATURE"),
        )
    except Exception as exc:  # e.g. malformed base_url
        raise RuntimeError(
            f"Failed to build OpenAI-compatible model {model_name!r} against "
            f"{OPENAI_BASE_URL!r}. Check OPENAI_BASE_URL / OPENAI_MODEL in .env."
        ) from exc


# Provider name -> builder. New backend = one builder + one entry here.
_BUILDERS = {
    "local": _build_ollama,
    "openai": _build_openai,
}


def build_chat_model(model_name: str | None = None) -> BaseChatModel:
    """Build (or return a cached) chat model for ``model_name``.

    The backend is chosen by ``LLM_PROVIDER``: ``local`` -> Ollama,
    ``openai`` -> any OpenAI-compatible endpoint. The first call imports the
    provider package and constructs the client; later calls return the same
    instance, so every agent shares a single LLM connection.

    Args:
        model_name: Which model to build. If ``None``, falls back to
            ``OPENAI_MODEL`` (provider ``openai``) or ``OLLAMA_MODEL`` (``local``).

    Returns:
        A configured :class:`BaseChatModel`.

    Raises:
        ValueError: If ``LLM_PROVIDER`` is not a known provider.
        ImportError: If the provider package (e.g. ``langchain-ollama``) is not installed.
        RuntimeError: If required config is missing or the model cannot be built.
    """
    if PROVIDER not in _BUILDERS:
        raise ValueError(f"Unknown LLM_PROVIDER {PROVIDER!r}; expected one of {sorted(_BUILDERS)}.")

    if model_name is None:
        model_name = DEFAULT_OPENAI_MODEL if PROVIDER == "openai" else DEFAULT_MODEL

    cache_key = (PROVIDER, model_name)
    existing = _instances.get(cache_key)
    if existing is not None:
        return existing

    # Import lazily so `import src.core.llm` never fails on a missing provider.
    model = _BUILDERS[PROVIDER](model_name)
    _instances[cache_key] = model
    return model


def reset() -> None:
    """Drop all cached model instances (mainly for tests / hot reload)."""
    _instances.clear()
