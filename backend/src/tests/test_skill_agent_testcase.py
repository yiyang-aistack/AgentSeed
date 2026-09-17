"""Tests for :mod:`src.agents.samples.skillAgent_testcase`.

This graph's expertise lives on disk, so the failure modes worth guarding are
filesystem ones — a skill file that no longer parses, a root that moved, a
sandbox that stops sandboxing. All of them are *silent* at runtime: deepagents
skips a SKILL.md whose front matter is malformed, and the model then simply
never learns that skill exists. Hence the explicit parse assertions below.

Nothing here touches the network: importing the module reads a directory and a
few small files, and ``build_chat_model`` constructs its client lazily.
"""

from __future__ import annotations

import pytest
import yaml
from src.agents.samples import skillAgent_testcase as mod

# ---------------------------------------------------------------------------
# Root resolution and backend construction
# ---------------------------------------------------------------------------


def test_skills_root_is_the_workspace_testcase_library():
    """Anchored to __file__, so it cannot drift with the CWD."""
    assert mod.skills_root.is_dir()
    assert mod.skills_root.parts[-2:] == ("workspace", "testcase")
    assert (mod.skills_root / "skills").is_dir()


def test_skills_backend_is_confined_to_the_root():
    # FilesystemBackend exposes the root as ``cwd`` — it is the resolve base for
    # both host paths and the virtual ones the model sees.
    assert mod.skills_backend.cwd == mod.skills_root
    assert mod.skills_backend.virtual_mode is True


def test_backend_reads_inside_the_root():
    result = mod.skills_backend.read("/skills/test-case-design/SKILL.md")
    assert result.error is None
    assert "name: test-case-design" in result.file_data["content"]


@pytest.mark.parametrize(
    "path",
    ["/../../.env", "/../.env", "/skills/../../../.env"],
)
def test_backend_refuses_to_escape_the_root(path):
    """The security property the module docstring claims: .env is unreachable."""
    with pytest.raises(ValueError, match="Path traversal not allowed"):
        mod.skills_backend.read(path)


# ---------------------------------------------------------------------------
# The skill library actually loads
# ---------------------------------------------------------------------------

_SKILL_DIRS = sorted(p.parent.name for p in mod.skills_root.glob("skills/*/SKILL.md"))


def test_library_is_not_empty():
    assert _SKILL_DIRS, "no SKILL.md found — the agent would run with no skills"


@pytest.mark.parametrize("name", _SKILL_DIRS)
def test_skill_front_matter_parses_and_matches_its_directory(name):
    """deepagents validates both, and skips the skill silently on mismatch."""
    raw = (mod.skills_root / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    # Byte 0, not "somewhere near the top": a leading blank line or heading
    # makes the front matter invisible to the parser.
    assert raw.startswith("---\n"), f"{name}: front matter must start at byte 0"
    _, front, body = raw.split("---", 2)
    meta = yaml.safe_load(front)
    assert meta["name"] == name
    assert meta["description"].strip()
    # Non-ASCII hyphens have bitten these files before (U+2011 vs ASCII `-`).
    assert "‑" not in meta["name"]
    assert body.strip(), f"{name}: empty body — nothing for the model to read"


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_middlewares_share_the_one_backend():
    from deepagents.middleware.filesystem import FilesystemMiddleware
    from deepagents.middleware.skills import SkillsMiddleware

    filesystem, skills = mod._middleware()
    assert isinstance(filesystem, FilesystemMiddleware)
    assert isinstance(skills, SkillsMiddleware)
    assert filesystem.backend is mod.skills_backend
    assert skills._backend is mod.skills_backend


def test_filesystem_tools_are_read_only():
    """This graph is published over HTTP; it must not be able to write or exec.

    Asserted on the middleware the agent is actually built with, not on a
    freshly constructed one: ``FilesystemMiddleware`` defaults to exposing the
    *whole* toolset, so passing ``tools=`` is the only thing standing between
    this agent and ``write_file`` / ``execute``.
    """
    from deepagents.middleware.filesystem import FilesystemMiddleware

    default = {t.name for t in FilesystemMiddleware(backend=mod.skills_backend).tools}
    assert {"write_file", "edit_file", "delete", "execute"} <= default

    wired = {t.name for t in mod._middleware()[0].tools}
    assert wired == set(mod._READ_ONLY_TOOLS)


def test_skills_source_exists_in_the_backend():
    for source in mod._SKILL_SOURCES:
        listing = mod.skills_backend.ls(source.rstrip("/") or "/")
        assert listing.error is None, f"{source} is not visible to the backend"
        assert any(e["is_dir"] for e in listing.entries), f"{source} holds no skills"


def test_system_prompt_inlines_only_the_policy_not_the_skill_library():
    """Progressive disclosure: skill *bodies* must not be preloaded."""
    prompt = mod._system_prompt()
    assert "QA engineer" in prompt
    assert "Review Policy" in prompt  # the inlined repo-wide policy
    for name in _SKILL_DIRS:
        body = (mod.skills_root / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        marker = next(
            line for line in body.splitlines() if len(line) > 40 and not line.startswith("#")
        )
        assert marker not in prompt, f"{name}: body leaked into the system prompt"


# ---------------------------------------------------------------------------
# The graph langgraph_api will serve
# ---------------------------------------------------------------------------


def test_agent_is_a_real_module_level_attribute():
    """`module.__dict__[var]` — a lazy PEP 562 export would read as missing."""
    assert "skill_testcase_agent" in vars(mod)
    assert hasattr(mod.skill_testcase_agent, "invoke")
    assert "skill_testcase_agent" in mod.__all__
