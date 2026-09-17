---
name: review_policy
description: Code/agent output review guidance
tools: []
---
# Review Policy

When you review any generated output (code diff, text, or a workflow result),
apply these rules:

1. **Minimal, idempotent changes** — prefer the smallest correct change; do not
   reformat or touch unrelated code.
2. **Single source of truth** — avoid duplicating config/logic that already lives
   in a canonical location (e.g. reuse `src.core.llm`, `capabilities`, registry).
3. **Lazy & safe at import** — do heavy IO/network only when actually needed, never
   as a module-import side effect.
4. **Explicit errors beat silent fallbacks** — raise with an actionable message
   rather than returning empty/None quietly.
5. **One concept, one directory** — do not reintroduce overlapping agent folders;
   reuse `src.agents` building blocks and `capabilities.*`.

End every review note with a concrete, one-line recommendation.
