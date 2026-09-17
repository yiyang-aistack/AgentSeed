"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

Skill-backed agent without deepAgent middleware — its expertise is a markdown
asset, not code in this file.

# How the two skill agents in this folder differ — same dimensions as before, laid
# out vertically so every line stays readable:
#
#   Skill Loading Mode   here: the full text of every skill is concatenated into
#                        the system prompt (direct inline).
#                        skillAgent_testcase.py: progressive disclosure — only
#                        names & descriptions are shown, the body is fetched with
#                        read_file on demand.
#   Skill Source         here: src.capabilities.skills.get_texts()
#                        testcase: deepagents.middleware.skills.SkillsMiddleware
#   Skill Storage Path   here: capabilities/skills/entries/*.md (project-level)
#                        testcase: src/workspace/testcase/skills/ (workspace dir)
#   Dependency Overhead  here: zero — a plain file read, no extra middleware.
#                        testcase: deepagents FilesystemBackend + two middlewares.
#   Skill Scale          here: a small set of permanently relevant skills.
#                        testcase: large, multi-scenario skill libraries.
#   Token Cost           here: grows with every skill added.
#                        testcase: scales without bound — only index tokens are
#                        charged per request.


The three capability layers are orthogonal, and each sample in this folder shows
one of them. ``localAgent`` shows the **tool registry**; this sample shows the
**skill loader** (``src.capabilities.skills``). A skill is a prompt/knowledge
asset stored as markdown under ``capabilities/skills/entries/``; the agent pulls
it by name and never carries the guidance inline. Here the asset is
``functional_testcase.md`` — a functional test-case design playbook (equivalence
partitioning, boundary value analysis, decision tables, …).

Two things this sample demonstrates that the others do not:

1. **Skills compose.** ``get_texts`` is called with two entries —
   ``functional_testcase`` (domain methodology) and ``review_policy`` (the
   repository-wide review rules). Both bodies are concatenated into one system
   prompt, so a project-wide policy can be layered under a task-specific one
   without either asset knowing about the other.
2. **Editing the prompt does not touch Python.** Rewording the playbook, or
   swapping it for another skill, is a markdown edit. ``get_texts`` strips the
   YAML front matter, so only the body reaches the model.

Relationship to ``workflows/testcase``
--------------------------------------
``workflows.testcase:testcase_agent`` is a *business-line delivery* — it exists to
be called. This file is a *framework sample* under ``agents/samples/`` whose job is
to show how the skills layer is bound. They deliberately do not share code:
``testcase_agent`` carries its instructions inline, this one loads them from an
asset. The playbook itself lives in exactly one place, so either could load
``functional_testcase`` without duplicating it — see the repo's
"one concept, one directory" rule.

Importing this module has no *network* side effects: no Ollama or API call is
made, only a ``ChatModel`` object is constructed through the memoized
``src.core.llm`` factory. The compiled agent is exported as a **real
module-level attribute** because ``langgraph_api`` resolves registered graphs
with ``module.__dict__[spec.variable]`` — a PEP 562 ``__getattr__`` lazy export
is invisible to it and makes the server fail at startup with
"Could not find graph".
"""

from __future__ import annotations

from src.capabilities.skills import get_texts
from src.capabilities.tools import builtin

# Skill asset names (file stems under capabilities/skills/entries/), in the order
# they are layered into the system prompt: project-wide policy first, then the
# task-specific playbook that refines it.
_SKILLS = ["functional_testcase", "review_policy"]


def _system_prompt() -> str:
    """Assemble the system prompt from framework skill assets.

    ``get_texts`` raises ``KeyError`` naming the missing entry if an asset is
    renamed or deleted, so a typo here fails loudly at import rather than
    producing an agent that silently lost its instructions.
    """
    parts = [
        "You are a QA engineer specialising in functional test design. Given a "
        "feature description or a requirement, you produce concrete, executable "
        "functional test cases with explicit test data and observable expected "
        "results. You may use the shared tools when the task needs them.",
        "",
        # Front matter already stripped by the loader; bodies only.
        "Apply the following playbook:",
        *get_texts(_SKILLS),
    ]
    return "\n".join(parts)


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import)."""
    from langchain.agents import create_agent

    from src.core.llm import build_chat_model

    return create_agent(
        model=build_chat_model(),  # shared, memoized — see src.core.llm
        # current_date keeps date-stamped output (test-plan revisions, run dates)
        # honest instead of letting the model guess "today".
        tools=builtin(["current_date"]),
        system_prompt=_system_prompt(),
    )


# Real module-level attribute — see the module docstring for why this cannot be lazy.
skill_testcase_agent = _build_agent()


__all__ = ["skill_testcase_agent"]
