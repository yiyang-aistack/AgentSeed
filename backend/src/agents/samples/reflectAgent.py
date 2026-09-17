"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

Reflect/Revise agent — a hand-built LangGraph StateGraph (sample).

Relocated to ``agents/samples`` during the framework restructure. Demonstrates:
- explicit, typed shared State with per-key semantics;
- multiple nodes (LLM *lang* node + pure-logic *review* node);
- conditional edge + cycle with bounded attempts (no infinite loops);
- model construction deferred to the shared ``src.core.llm`` factory.

Task: given a short topic description, iterate a one-line marketing catchphrase
until it (a) contains the topic keyword, or (b) hits the attempt cap.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.core.llm import build_chat_model

MAX_ATTEMPTS = 3


class ReflectState(TypedDict):
    """Shared graph state.

    - ``task``:     the user's source text (read-only input).
    - ``draft``:    the latest generated catchphrase.
    - ``attempts``: number of draft iterations performed so far.
    - ``reviews``:  human-readable log of why we re-iterated (observability).
    - ``done``:     whether the review accepts the current draft (drives the loop).
    """

    task: str
    draft: str | None
    attempts: int
    reviews: list[str]
    done: bool


_SYSTEM = (
    "You craft one-line marketing catchphrases for a product/topic given by the "
    "user. Reply with ONLY the catchphrase text, no quotes or extra prose."
)


def _draft_task_prompt(task: str, reviews: list[str] | None) -> str:
    """Build the user prompt: the source text plus any revision feedback."""
    prompt = task
    if reviews:
        prompt += (
            "\n\nYour previous attempts failed for these reasons. Fix them "
            "explicitly:\n- " + "\n- ".join(reviews[-2:])
        )
    return prompt


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def draft_node(state: ReflectState) -> dict:
    """Call the (cached) LLM to produce or revise the catchphrase."""
    model = build_chat_model()
    user_msg = _draft_task_prompt(state["task"], state.get("reviews"))
    result = model.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=user_msg)])
    content = result.content
    if isinstance(content, list):
        text = "".join(c if isinstance(c, str) else getattr(c, "text", "") for c in content)
    else:
        text = str(content)
    return {
        "draft": text.strip(),
        "attempts": state.get("attempts", 0) + 1,
        "done": False,
    }


def review_node(state: ReflectState) -> dict:
    """Pure-python gatekeeper that decides whether the draft is acceptable.

    Sets ``done=True`` (accept and finish) when we have used all attempts OR when
    the topic's first keyword appears in the draft; otherwise appends a concrete,
    deterministic hint so the next draft can fix it.
    """
    draft: str = (state.get("draft") or "").strip()
    word = (state["task"].strip().split() or [""])[0].lower()
    attempts = state.get("attempts", 0)

    if attempts >= MAX_ATTEMPTS or (word and word in draft.lower()):
        return {"reviews": state.get("reviews") or [], "done": True}

    reasons = list(state.get("reviews") or [])
    if not draft:
        reasons.append("The catchphrase came back empty.")
    elif len(draft) > 180:
        reasons.append("Too long: keep it a single line under 180 characters.")
    else:
        reasons.append(f"It does not mention the topic {state['task']!r} clearly.")
    return {"reviews": reasons, "done": False}


def route_after_review(state: ReflectState) -> str:
    if state.get("done"):
        return END
    return "draft"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

builder = StateGraph(ReflectState)

builder.add_node("draft", draft_node)
builder.add_node("review", review_node)
builder.add_edge(START, "draft")
builder.add_edge("draft", "review")
builder.add_conditional_edges("review", route_after_review, {END: END, "draft": "draft"})

reflect_agent = builder.compile()
