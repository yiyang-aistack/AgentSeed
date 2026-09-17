#!/usr/bin/env python3

"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.
"""

"""
AgentSeed customized base on LangGraph API Server is AI Agent Application Framework
to quick setup Agent application

The purpose of AgentSeed is designed for quick setup of AI Agents Application
for solopreneur or firms staff to build and deploy AI Agents in minutes to deal
with various business scenarios.

AgentSeed is built up based on LangGraph API server locally (inmemory) using
uvicorn directly as script.

Repository layout (this file lives in ``backend/``)
--------------------------------------------------
    <repo>/backend/main.py        <- entrypoint (this script)
    <repo>/backend/src/**         <- framework packages: core / agents / capabilities / workflows
    <repo>/frontend/**            <- Next.js chat UI (independent app, talks HTTP only)
    <repo>/.env                   <- static config (single source of truth)
    <repo>/agentConfig.yaml       <- which graphs the server exposes
    <repo>/logs/                  <- daily-rotating runtime logs

Launch from the repository root:  uv run backend/main.py
"""

import os
import sys

"""
 ### Runtime Environment Compatibility ###
  > Force UTF-8 mode on Windows to avoid GBK (cp936) encoding issues.
  > Linux / macOS default locale is already UTF-8 — skip to avoid an extra fork.
  > Set SKIP_UTF8_RESTART=1 to bypass (useful when debugging with pdb / pytest).
"""
# A redirected stdout/stderr (`python backend/main.py > run.log`, an IDE task that pipes the
# output, a service wrapper) uses the locale codec — cp936/GBK on a Chinese Windows — while the
# interactive console is always UTF-8. The emoji in the start-up messages below are not encodable
# there, and `UnicodeEncodeError` would kill the launcher before it starts. Keep the native codec
# (so a terminal is untouched) and only soften the error handler.
for _stream in (sys.stdout, sys.stderr):
    _encoding = (getattr(_stream, "encoding", None) or "").replace("-", "").lower()
    if _encoding and _encoding != "utf8":
        try:
            _stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

if (
    sys.platform == "win32"
    and os.environ.get("PYTHONUTF8") != "1"
    and os.environ.get("SKIP_UTF8_RESTART") != "1"
):
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    print("🔄 Restarting with UTF-8 mode (PYTHONUTF8=1)...\n")
    sys.stdout.flush()
    import subprocess

    # Propagate the child's exit code: the parent is only a shim, so a failed start
    # (missing dependency, port in use) must not be masked as a success here.
    sys.exit(
        subprocess.run(
            [sys.executable] + sys.argv, env=os.environ.copy(), stdin=sys.stdin
        ).returncode
    )


import importlib.util
import json
from pathlib import Path

# --- Path anchoring ---------------------------------------------------------
# Everything is derived from THIS file's location, so AgentSeed behaves the same
# no matter which directory the launcher was invoked from.
BACKEND_DIR = Path(__file__).resolve().parent  # <repo>/backend
PROJECT_ROOT = BACKEND_DIR.parent  # <repo> - owns .env / agentConfig.yaml / logs/
SRC_DIR = BACKEND_DIR / "src"  # <repo>/backend/src - import root of the graphs

# Two entries are required because two import styles are in play:
#   * ``src.*``                      (framework code, e.g. src.core.llm)  -> <repo>/backend
#   * ``agents.*`` / ``workflows.*`` (graph specs in agentConfig.yaml)    -> <repo>/backend/src
for _path in (str(BACKEND_DIR), str(SRC_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

"""
 ### Interpreter Guard ###
  > Launching with an unrelated interpreter (system Python, conda base, an IDE SDK that was
    never synced) misses every dependency: uvicorn's reloader boots fine, then the worker
    process dies with a raw `ModuleNotFoundError: No module named 'langgraph_api'`.
  > This guard runs BEFORE uvicorn is imported and either restarts once inside the project
    environment `<repo>/.venv` (created by `uv sync` — same self-restart pattern as the
    UTF-8 block above), or stops with the exact command that fixes it.
  > `find_spec` is used instead of `import` on purpose: `langgraph_api` reads its whole
    configuration from the environment at import time, so it may only be imported inside
    the worker, i.e. after .env has been loaded.
  > Set SKIP_VENV_RESTART=1 to forbid the restart (handy under a debugger). It must be set
    in the real process environment — .env is loaded later, so it cannot switch this off.
"""
# (import name, distribution name) of every third-party package the server cannot start without.
REQUIRED_DISTRIBUTIONS = (
    ("dotenv", "python-dotenv"),  # setup_environment(): load .env
    ("yaml", "pyyaml"),  # parse agentConfig.yaml
    ("uvicorn", "uvicorn"),  # uvicorn.run() below
    ("langchain", "langchain"),  # backend/src/agents/**: create_agent
    ("langgraph_api", "langgraph-api"),  # langgraph_api.server:app
    ("langgraph_runtime_inmem", "langgraph-runtime-inmem"),  # LANGGRAPH_RUNTIME_EDITION=inmem
)


def missing_distributions():
    """Distribution names of REQUIRED_DISTRIBUTIONS this interpreter cannot import."""
    return [
        dist for module, dist in REQUIRED_DISTRIBUTIONS if importlib.util.find_spec(module) is None
    ]


def project_interpreter():
    """Interpreter of the uv-managed environment (<repo>/.venv), or None when it was never
    synced."""
    for candidate in (
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
        PROJECT_ROOT / ".venv" / "bin" / "python",  # Linux / macOS
    ):
        if candidate.exists():
            return candidate
    return None


def ensure_project_environment():
    """Continue on a complete interpreter: restart inside <repo>/.venv, or fail fast with
    the remedy."""
    missing = missing_distributions()
    if not missing:
        return

    interpreter = project_interpreter()
    on_project_interpreter = (
        interpreter is not None and Path(sys.executable).resolve() == interpreter.resolve()
    )
    restart_forbidden = os.environ.get("SKIP_VENV_RESTART") == "1"

    if interpreter is not None and not on_project_interpreter and not restart_forbidden:
        print(
            f"🔄 Missing packages ({', '.join(missing)}) -> "
            "restarting inside the project environment:"
        )
        print(f"     {sys.executable}")
        print(f"  -> {interpreter}\n")
        sys.stdout.flush()
        os.environ["SKIP_VENV_RESTART"] = "1"  # one-shot marker: this restart can never loop
        import subprocess

        sys.exit(
            subprocess.run(
                [str(interpreter)] + sys.argv, env=os.environ.copy(), stdin=sys.stdin
            ).returncode
        )

    print(f"❌ Missing Python packages: {', '.join(missing)}")
    print(f"   Interpreter in use : {sys.executable}")
    if interpreter is not None:
        print(f"   Project environment: {interpreter}")
    print("   Fix (from the repository root):  uv sync   then   uv run backend/main.py")
    sys.exit(1)


# Fail on a wrong interpreter here, not as a traceback inside the reload worker.
ensure_project_environment()

import uvicorn
from src.core.logConfig import get_uvicorn_log_config as log_config

"""
 ### Configuration Variables ###
 By default, configration are loaded from two level:
  > Application level  : Application related environment variables are loaded from .env file.
  > Business level     : Business related environment variables are loaded from agentConfig.yaml.
"""


def setup_environment():

    # Anchor the working directory to the repository root: runtime artifacts
    # (langgraph_api file persistence, a relative LOG_DIR) then always land next to
    # .env / agentConfig.yaml, no matter which directory the launcher was run from.
    os.chdir(PROJECT_ROOT)

    # Load graphs from agentConfig.yaml (yaml supports comments, better for multi-agent config)
    config_path = PROJECT_ROOT / "agentConfig.yaml"
    graphs = {}

    if config_path.exists():
        try:
            import yaml
        except ImportError:
            print("❌ pyyaml not installed in this interpreter, cannot load agentConfig.yaml")
            print("   Fix (from the repository root):  uv sync   then   uv run backend/main.py")
            sys.exit(1)
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            graphs = config.get("graphs", {}) or {}

    # Load .env first so it becomes the single source of truth for static config.
    # override=True so .env wins over any pre-existing process env (matches user intent).
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
        except ImportError:
            print("❌ python-dotenv not installed in this interpreter, cannot load .env")
            print("   Fix (from the repository root):  uv sync   then   uv run backend/main.py")
            sys.exit(1)
        load_dotenv(env_file, override=True)
        print("✅ Loaded environment from .env")

    # Runtime-derived values: cannot live in static .env.
    # LANGGRAPH_API_URL derives from HOST & PORT; LANGSERVE_GRAPHS derives from agentConfig.yaml.
    # setdefault => .env can still override these if user really wants to.
    # PORT must come from .env — no hardcoded fallback (SSOT).
    port = os.getenv("PORT")
    if not port:
        print("❌ 'Port' is not set in .env. Add e.g. `Port=2026` to .env and retry.")
        sys.exit(1)
    host = os.getenv("HOST") or "0.0.0.0"
    os.environ.setdefault("LANGGRAPH_API_URL", f"http://{host}:{port}")
    os.environ.setdefault("LANGSERVE_GRAPHS", json.dumps(graphs) if graphs else "{}")


"""Start the server"""


def startup():
    print(" ***** Starting API Server *****")

    # Load Environment Variables
    setup_environment()

    # Print server information (host/port from .env via setup_environment)
    host = os.getenv("HOST") or "0.0.0.0"
    port = os.getenv("PORT")  # validated non-None in setup_environment
    print("\n" + "=" * 60)
    print(f"📂 Project root: {PROJECT_ROOT}")
    print(f"🐍 Interpreter: {sys.executable}")
    print(f"📍 Server URL: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"💚 Health Check: http://localhost:{port}/ok")
    print("=" * 60)

    # Start the server directly
    try:
        uvicorn.run(
            "langgraph_api.server:app",
            host=host,
            port=int(port),
            reload=True,
            access_log=False,
            log_config=log_config(),
            # Only the backend tree is watched, but the paths below must still be excluded:
            # a write there (a log line, `uv sync`, langgraph_api persistence) would otherwise
            # restart the server and cause a reload storm.
            #
            # KEEP THIS LIST CHEAP. uvicorn resolves every pattern in Config.__init__
            # (resolve_reload_patterns) *before* it binds the socket, and there:
            #   * a pattern that names a directory -> a single stat                  (cheap)
            #   * "<dir>/**" / "**/<name>/**"      -> globs that tree into thousands of
            #     directories and then compares every directory with every other one (O(n²)).
            # With the previous "<dir>/**" list that was 4,262 directories / 9.1M pair
            # comparisons (~10s+ of startup, minutes on a slow disk) — and once
            # `yarn install` has populated frontend/node_modules, ~50k directories /
            # hundreds of millions of comparisons, i.e. the server never gets to listen.
            # Hence: directory names + shallow file globs only. No "__pycache__" entry is
            # needed either: uvicorn only restarts on files matching "*.py", and a ".pyc"
            # never does.
            reload_dirs=[str(BACKEND_DIR)],
            reload_excludes=[
                "logs",  # runtime logs — a log write must never restart the server
                ".venv",  # virtual environment — rewritten by `uv sync`
                ".langgraph_api",  # langgraph_api file persistence
                "frontend",  # Next.js app (node_modules / .next)
                "node_modules",
                ".next",
                "*.log",
                "*.log.*",
                "*.tsbuildinfo",
                "*.py[cod]",
                "uv.lock",
            ],
        )
    except KeyboardInterrupt:
        print("\n AgentSeed Server stopped by user")
    except Exception as e:
        print(f"  AgentSeed Server failed to start: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    startup()
