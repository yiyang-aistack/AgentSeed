"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

Skill-backed test-design agent with deepAgent skill middleware — its expertise is
a library of ``SKILL.md`` assets on disk, published to the model by *progressive disclosure*.

# How the two skill agents in this folder differ — same dimensions as before, laid
# out vertically so every line stays readable:
#
#   Skill Loading Mode   here: progressive disclosure — only names & descriptions
#                        are shown, the body is fetched with read_file on demand.
#                        skillAgent_ts.py: the full text of every skill is
#                        concatenated into the system prompt (direct inline).
#   Skill Source         here: deepagents.middleware.skills.SkillsMiddleware
#                        testcase: src.capabilities.skills.get_texts()
#   Skill Storage Path   here: src/workspace/testcase/skills/ (workspace dir)
#                        testcase: capabilities/skills/entries/*.md (project-level)
#   Dependency Overhead  here: deepagents FilesystemBackend + two middlewares.
#                        testcase: zero — a plain file read, no extra middleware.
#   Skill Scale          here: large, multi-scenario skill libraries.
#                        testcase: a small set of permanently relevant skills.
#   Token Cost           here: scales without bound — only index tokens are
#                        charged per request.
#                        testcase: grows with every skill added.




There are two skill mechanisms in this repository and they answer different
questions:

* ``src.capabilities.skills`` (``get_texts``) — the lightweight, dependency-free
  path. It inlines a markdown asset straight into the system prompt. Good for a
  short, always-relevant policy: that is why ``review_policy`` is loaded that way
  here, and by ``workflows.testcase``.
* **this file** — the scenario library under ``src/workspace/testcase/skills/``,
  loaded through deepagents' ``SkillsMiddleware``. The model is shown only each
  skill's *name and description*; it pulls the full text with ``read_file`` when
  a task actually matches. That keeps a large, multi-scenario library out of
  every prompt, which is the whole point: the library can grow without every
  request paying for it.

Wiring, and why it is not just ``create_agent``:
------------------------------------------------
``create_agent`` in this repo's langchain has **no ``backend=`` parameter** (and
no ``**kwargs``), so the backend is handed to the middleware that actually uses
it. Two middlewares share one backend:

* ``FilesystemMiddleware`` — exposes the read tools. It is **required**, not
  optional: the skills prompt tells the model to load a skill body with
  ``read_file``, so without this middleware every skill would be announced and
  then be unreadable.
* ``SkillsMiddleware`` — builds the skill index and injects it into the prompt.

Only read-only tools are enabled (``ls`` / ``read_file`` / ``glob`` / ``grep``).
``write_file``, ``edit_file``, ``delete`` and ``execute`` are deliberately left
out: this graph is published over an HTTP API, and an agent that could rewrite
files or run shell commands under the workspace — or, with ``execute``, anywhere
on the host — is not something a test-case generator should be able to do. Reads
are additionally confined to ``skills_root`` by ``virtual_mode=True``, which
blocks ``..`` and absolute paths escaping the root, so ``.env`` at the repository
root is not reachable.

Importing this module touches no network and no API: it lists a directory and
reads a handful of small files. The compiled agent is exported as a **real
module-level attribute** because ``langgraph_api`` resolves registered graphs
with ``module.__dict__[spec.variable]`` — a PEP 562 ``__getattr__`` lazy export
is invisible to it and makes the server fail at startup with
"Could not find graph".
"""

from __future__ import annotations

from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend

from src.capabilities.skills import get_texts
from src.capabilities.tools import builtin

# ---------------------------------------------------------------------------
# Skill library root
# ---------------------------------------------------------------------------
# ``backend/src/workspace/testcase`` — the scenario library, one directory per
# skill, each holding a SKILL.md with ``name`` / ``description`` front matter.
# Resolved from __file__ rather than the CWD, because the server is documented to
# be started from the repository root but the path must not depend on that.
#   parents[0]=samples  [1]=agents  [2]=src  ->  <repo>/backend/src/workspace/testcase
skills_root = (Path(__file__).resolve().parents[2] / "workspace" / "testcase").resolve()

# Reads are confined to skills_root: virtual_mode blocks `..` and absolute paths
# that escape the root.
skills_backend = FilesystemBackend(root_dir=skills_root, virtual_mode=True)

# Read-only subset of the filesystem tools — see the module docstring for why
# write/edit/delete/execute are excluded.
_READ_ONLY_TOOLS = ["ls", "read_file", "glob", "grep"]

# Which sub-directory of skills_root holds the skills. Paths are virtual paths
# interpreted by skills_backend, not host paths.
_SKILL_SOURCES = ["/skills/"]

# Repo-wide policy, inlined through the lightweight loader (see the module
# docstring for why this one is not a scenario skill).
_POLICY_SKILL = "review_policy"

_SYSTEM_PROMPT = (
    "You are a QA engineer specialising in functional test design. Given a "
    "feature description, a requirement or a PRD, you produce concrete, "
    "executable test cases with explicit test data and observable expected "
    "results.\n\n"
    "The skills listed below are your working method for this task — consult the "
    "relevant ones before designing cases, and follow them rather than inventing "
    "your own structure. Check for an applicable skill even when the task looks "
    "routine."
)


def _middleware() -> list:
    """Build the two middlewares that share ``skills_backend``.

    Imported lazily so the module can be imported (and introspected) without the
    deepagents providers being pulled in eagerly, matching the rest of
    ``agents/samples``.
    """
    from deepagents.middleware.filesystem import FilesystemMiddleware
    from deepagents.middleware.skills import SkillsMiddleware

    return [
        # Order matters in the prompt: filesystem tools are advertised first, then
        # the skill index that tells the model to use them.
        FilesystemMiddleware(backend=skills_backend, tools=_READ_ONLY_TOOLS),
        SkillsMiddleware(backend=skills_backend, sources=_SKILL_SOURCES),
    ]


def _system_prompt() -> str:
    """Compose the system prompt: persona + the repo-wide review policy.

    ``get_texts`` raises ``KeyError`` naming the asset if it was renamed, so a
    typo fails loudly at import instead of shipping an agent that silently lost
    its instructions.
    """
    policy = get_texts([_POLICY_SKILL])[0]
    return f"{_SYSTEM_PROMPT}\n\nReview policy you must follow before your final answer:\n{policy}"


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import)."""
    from langchain.agents import create_agent

    from src.core.llm import build_chat_model

    return create_agent(
        model=build_chat_model(),  # shared, memoized — see src.core.llm
        # Scenario skills arrive via SkillsMiddleware; this registry tool stays
        # bound so date-stamped output (plan revisions, run dates) is honest
        # instead of guessed.
        tools=builtin(["current_date"]),
        middleware=_middleware(),
        system_prompt=_system_prompt(),
    )


# Real module-level attribute — see the module docstring for why this cannot be lazy.
skill_testcase_agent = _build_agent()


__all__ = ["skill_testcase_agent", "skills_root", "skills_backend"]
