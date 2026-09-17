# Skill Agent Samples — Comparison

This document compares two skill-backed agent implementations in this folder:

Any solopreneur are suggested to distinguish it for your delivery

| File | Description |
|------|-------------|
| `skillAgent_ts.py` | Skill-backed agent with **inline skill loading** (lightweight) |
| `skillAgent_testcase.py` | Skill-backed agent with **progressive disclosure** (scalable) |

---

## 1. What They Share

### Same Core Role
Both agents are **QA test-design specialists**. The system prompt persona is nearly identical:

> *"You are a QA engineer specialising in functional test design. Given a feature description or a requirement, you produce concrete, executable functional test cases..."*

### Same Build Skeleton
Both follow the same three-step construction pattern:

| Step | `skillAgent_ts.py` | `skillAgent_testcase.py` |
|------|:------------------:|:------------------------:|
| `_system_prompt()` | ✅ Assembles prompt | ✅ Assembles prompt |
| `_build_agent()`   | ✅ Lazy import + `create_agent` | ✅ Lazy import + `create_agent` |
| Module-level export | ✅ `skill_testcase_agent = _build_agent()` | ✅ `skill_testcase_agent = _build_agent()` |

### Same Tool Registration
Both register exactly one built-in tool:

```python
tools = builtin(["current_date"])
```

This keeps date-stamped output (test-plan revisions, run dates) honest instead of letting the model guess "today".

### Same LLM Factory
Both use the shared, memoized model builder:

```python
model = build_chat_model()  # src.core.llm
```

### Same Module-Level Export Pattern
Both export `skill_testcase_agent` as a **real module-level attribute**, not a PEP 562 `__getattr__` lazy export. This is required because `langgraph_api` resolves registered graphs via `module.__dict__[spec.variable]` — lazy exports are invisible to it and cause startup failure with *"Could not find graph"*.

### Same Top-Level Import Strategy
Both keep top-level imports lightweight (no network side effects). Heavy dependencies (`langchain`, `deepagents`) are imported lazily inside functions.

---

## 2. How They Differ

### Core Difference: Skill Loading Mechanism

This is the architectural heart of both files — they demonstrate two completely different skill-layer designs.

| Dimension | `skillAgent_ts.py` | `skillAgent_testcase.py` |
|-----------|--------------------|--------------------------|
| **Loading style** | **Inline** — full skill bodies are concatenated directly into the system prompt | **Progressive disclosure** — only skill name + description are shown; the model fetches full text on demand via `read_file` |
| **Skill source** | `src.capabilities.skills.get_texts()` | `deepagents.middleware.skills.SkillsMiddleware` |
| **Skill location** | `capabilities/skills/entries/*.md` (project-level) | `src/workspace/testcase/skills/` (workspace directory) |
| **Dependency cost** | Zero (plain file read, no extra middleware) | Requires deepagents `FilesystemBackend` + two Middlewares |
| **Best for** | Small number of always-relevant skills | Large, growing scenario library |
| **Token cost** | Linear with skill count — every request pays for everything | Fixed per request; skill library can grow unbounded |

---

### 2.1 Middleware Layer

**`skillAgent_ts.py` — no middleware at all:**

```python
return create_agent(
    model=build_chat_model(),
    tools=builtin(["current_date"]),
    system_prompt=_system_prompt(),
    # note: no `middleware=` kwarg
)
```

**`skillAgent_testcase.py` — two middlewares sharing one backend:**

```python
def _middleware() -> list:
    return [
        FilesystemMiddleware(backend=skills_backend, tools=_READ_ONLY_TOOLS),
        SkillsMiddleware(backend=skills_backend, sources=_SKILL_SOURCES),
    ]
```

Order matters: filesystem tools are advertised first, then the skill index tells the model *when* to use them.

---

### 2.2 Skill Security Boundary

| Dimension | `skillAgent_ts.py` | `skillAgent_testcase.py` |
|-----------|--------------------|--------------------------|
| **Filesystem access** | None (prompt assets only) | Yes — strictly sandboxed |
| **Backend** | N/A | `FilesystemBackend(root_dir=..., virtual_mode=True)` |
| **Tool whitelist** | Only `current_date` | `["ls", "read_file", "glob", "grep"]` |
| **Write capabilities** | N/A | **Explicitly excluded**: `write_file`, `edit_file`, `delete`, `execute` |
| **Path escape protection** | N/A | `virtual_mode=True` blocks `..` and absolute paths escaping the root |

This is unique to the testcase variant — the agent is exposed over an HTTP API, so a test-case generator must never be able to rewrite files or run shell commands.

---

### 2.3 System Prompt Assembly

**`skillAgent_ts.py` — directly concatenates two skill bodies:**

```python
_SKILLS = ["functional_testcase", "review_policy"]
parts = [persona, "", "Apply the following playbook:", *get_texts(_SKILLS)]
```

Order: global policy first, task-specific playbook second.

**`skillAgent_testcase.py` — only the policy is inlined; scenario skills are injected by middleware:**

```python
_POLICY_SKILL = "review_policy"
# ... scenario skills arrive via SkillsMiddleware, not here
```

---

### 2.4 Path Resolution

**`skillAgent_ts.py`** — no path handling (skills resolved internally by `get_texts`).

**`skillAgent_testcase.py`** — resolves the workspace relative to `__file__`, not CWD:

```python
skills_root = (Path(__file__).resolve().parents[2] / "workspace" / "testcase").resolve()
# parents[0]=samples  [1]=agents  [2]=src  ->  <repo>/backend/src/workspace/testcase
```

The server is documented to start from the repo root, but the code must not *depend* on that.

---

### 2.5 Exports

| Dimension | `skillAgent_ts.py` | `skillAgent_testcase.py` |
|-----------|--------------------|--------------------------|
| `__all__` | `["skill_testcase_agent"]` | `["skill_testcase_agent", "skills_root", "skills_backend"]` |

The testcase variant also exports `skills_root` and `skills_backend` for external introspection (debugging, reuse).

---

## 3. Design Intent Summary

| Dimension | `skillAgent_ts.py` | `skillAgent_testcase.py` |
|-----------|--------------------|--------------------------|
| **Role** | Framework sample | Deployable business agent |
| **Skill scale assumption** | Small (2 skills) | Large (scenario library, growing) |
| **Security level** | Basic | High (read-only FS + path sandbox) |
| **Cost sensitivity** | Low (fixed token per request) | High (progressive disclosure controls growth) |
| **Evolution direction** | Stay simple | Add more scenario `SKILL.md` files |

**In one line:** `skillAgent_ts.py` demonstrates the lightweight inline pattern (good for a small, fixed skill set), while `skillAgent_testcase.py` demonstrates the progressive disclosure pattern (good for a large, dynamically extensible skill library). They share the same agent construction skeleton but make fundamentally different tradeoffs at the skill-loading layer.
