---
name: functional_testcase
description: Functional test-case design playbook (techniques, format, quality rules)
tools: []
---
# Functional Test Case Design

You are designing **functional** test cases: they verify *what* the system does
against its stated requirements, not how it does it internally. Never propose a
case whose outcome depends on implementation detail.

## Step 1 — Pin the requirement down

Before writing any case, restate the feature in one sentence of the form
*"Given <state>, when <action>, then <observable result>"*. If you cannot, the
requirement is ambiguous — list the ambiguity as an open question instead of
guessing, because a test written on a guess encodes the wrong expectation.

Extract every **input**, every **decision the system makes**, and every
**observable output**. These are the only things a functional case may assert on.

## Step 2 — Pick techniques per input

Choose deliberately; do not just list "happy path" variants. For each input or
rule, name the technique you are applying:

- **Equivalence partitioning** — one representative per class of inputs the
  system treats identically (valid, invalid, empty, wrong type).
- **Boundary value analysis** — for every ordered or numeric range, test the
  minimum, minimum−1, maximum, maximum+1. Boundary defects dominate real bug
  reports; always include them for length, count, amount, date and rate limits.
- **Decision table** — when behaviour depends on a combination of conditions,
  enumerate the condition combinations and their expected actions so no
  combination is silently skipped.
- **State transition** — when the object has states (draft → submitted →
  approved), test each valid transition *and* the invalid ones (approve an
  already-approved record) — invalid transitions are where such systems break.
- **Pairwise / orthogonal** — when independent parameters multiply into too many
  combinations, cover all pairs rather than the full cross-product, and say so.
- **Error guessing** — past-defect patterns: duplicate submission, concurrent
  edit, timeout then retry, unicode/whitespace-only input, leading zeros, and
  the largest plausible payload.

## Step 3 — Write each case in this exact shape

```
ID:          TC-<AREA>-<NNN>
Title:       <one line, states the condition — not "test login">
Priority:    P0 | P1 | P2
Technique:   <from Step 2>
Precondition: <state that must hold before the case runs>
Steps:       1. <action>  2. <action>
Test data:   <concrete values — never "some invalid input">
Expected:    <observable, checkable result>
```

Field rules that make cases usable by someone who did not write them:

- **Concrete test data, always.** "Enter an invalid email" is not testable;
  `a@b` (no TLD) is.
- **One case, one behaviour.** If a case needs "and" in its Title, split it. A
  failing case must point at a single cause.
- **Independently executable.** No case may depend on another having run. Repeat
  shared setup in the Precondition instead of chaining.
- **Expected result states what is observable** — a message, a status, a stored
  value. "Works correctly" is not an expected result.
- **Priority by risk, not by order.** P0 = data loss / security / a blocked core
  flow. P2 = cosmetic or rare.

## Step 4 — Cover these categories or say why not

Happy path · invalid input · boundaries · empty and null · duplicate submission ·
permissions (unauthorised and wrong-role) · concurrency where shared state
exists · failure handling when a dependency is unavailable.

State explicitly which of these you skipped and why — a silent gap reads as
coverage that does not exist.

## Anti-patterns to avoid

- Enumerating every possible input instead of the classes and boundaries.
- Asserting on log text, internal method names, or DB rows: those are unit- or
  integration-level concerns and they make the case fail on refactors.
- Bundling ten assertions into one case so a failure report is ambiguous.
- Copying the requirement sentence into Expected — it must describe the
  *result*, not restate the input.
- Inventing requirements the description never stated. Flag the gap instead.

## Output

Lead with a one-line coverage summary (how many cases, which techniques, which
categories were skipped). Then the numbered cases. Close with the open questions
from Step 1, if any.
