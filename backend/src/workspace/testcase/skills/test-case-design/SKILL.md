---
name: test-case-design
description: "Core test-design Skill that delivers a complete test-case design methodology. Activated when test cases need to be designed for specific functional points. It covers six classic design techniques: Equivalence Partitioning, Boundary Value Analysis, Decision Table, State Transition, Scenario Method, and Error Guessing, together with full case templates and design specifications."
---

# Test-Case Design Methodology Skill
## Activation Scenarios
- Test cases need to be generated for specific functional points
- The user requests test-case design for a module or API
- Evaluating whether existing test cases cover sufficient design dimensions

---
## Six Test-Design Techniques
### Technique 1: Equivalence Partitioning
**Principle**: Divide the input domain into several equivalence classes; test one representative value from each class.
```
Application Steps:
1. Identify all input fields
2. Divide valid equivalence classes and invalid equivalence classes for each field
3. Pick one representative value from each equivalence class

Example- Username field (4-20 characters in length):
┌─────────────────┬──────────────────┬─────────────────────┐
│ Equivalence Class│ Category         │ Representative Value│
├─────────────────┼──────────────────┼─────────────────────┤
│ 4-20 characters  │ ✅ Valid Class   │ "testuser" (8 chars)│
│ 1-3 characters   │ ❌ Invalid Class │ "abc" (3 chars)     │
│ 21+ characters   │ ❌ Invalid Class │ "a" ×21 (21 chars)  │
│ Contains special characters │ ❌ Invalid Class │ "user@name" │
│ Pure digits      │ ⚠️ Undetermined Class │ "12345678"    │
└─────────────────┴──────────────────┴─────────────────────┘
```

### Technique 2: Boundary Value Analysis
**Principle**: Select values at equivalence-class boundaries, since defects frequently occur at boundaries.
```
Boundary-value selection rule (for range [min, max]):
  min-1  |  min  |  min+1  |  mid-value  |  max-1  |  max  |  max+1

Example- Age range (18-65 years old):
┌──────┬────────────────────────────────────────────────────┐
│ Value│ Case Description                                   │
├──────┼────────────────────────────────────────────────────┤
│ 17   │ Lower boundary-1 (Expected: reject, prompt "Age does not meet requirements") │
│ 18   │ Lower boundary (Expected: accept)                  │
│ 19   │ Lower boundary+1 (Expected: accept)                 │
│ 41   │ Mid-value (Expected: accept)                       │
│ 64   │ Upper boundary-1 (Expected: accept)                 │
│ 65   │ Upper boundary (Expected: accept)                   │
│ 66   │ Upper boundary+1 (Expected: reject)                 │
│ 0    │ Special zero-value handling (Expected: reject)      │
│ -1   │ Special negative-value handling (Expected: reject)   │
└──────┴────────────────────────────────────────────────────┘

String boundaries: empty string("") / single character / max length / max length+1 / over-length string
Numeric boundaries: 0 / negative numbers / maximum integer / decimal precision boundaries
Date boundaries: start-end year / 28/29/30/31 days of month / leap years / year-end rollover
```

### Technique 3: Decision Table
**Principle**: Test business rules with multi-condition combinations by enumerating condition combinations.
```
Example- Coupon usage rules:
Conditions:
  C1: Order amount ≥ 100 CNY
  C2: User is a member
  C3: Coupon is not expired

Results:
  A1: Coupon can be applied
  A2: Coupon cannot be applied
  A3: Show threshold discount prompt

┌────┬────┬────┬────┬────┬────┬────┬────┬────┐
│    │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │
├────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ C1 │ T  │ T  │ T  │ T  │ F  │ F  │ F  │ F  │
│ C2 │ T  │ T  │ F  │ F  │ T  │ T  │ F  │ F  │
│ C3 │ T  │ F  │ T  │ F  │ T  │ F  │ T  │ F  │
├────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ A1 │ ✅ │ ❌ │ ❌ │ ❌ │ ❌ │ ❌ │ ❌ │ ❌ │
│ A2 │    │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │
└────┴────┴────┴────┴────┴────┴────┴────┴────┘

→ Generate one test case per column (columns with identical rules may be merged)
```

### Technique 4: State Transition
**Principle**: Test object-oriented state machines and verify correctness of state transitions.
```
Applicable targets: orders, user accounts, approval workflows, work-ticket statuses

State-diagram example- Order status:
[Pending Payment] --Payment Succeeded--> [Awaiting Shipment]
[Pending Payment] --Cancel Order--> [Cancelled]
[Pending Payment] --Payment Timeout--> [Closed]
[Awaiting Shipment] --Merchant Ships Goods--> [Awaiting Receipt]
[Awaiting Shipment] --Cancel Request--> [Refunding]
[Awaiting Receipt] --Confirm Receipt--> [Completed]
[Awaiting Receipt] --Apply for Return--> [Refunding]
[Refunding] --Refund Succeeded--> [Refunded]

Test-case design:
1. Positive flow: Pending Payment → Awaiting Shipment → Awaiting Receipt → Completed
2. Cancellation flow: Pending Payment → Cancelled (check whether cancel button disappears)
3. Timeout flow: Pending Payment → Closed (triggered by timeout)
4. Refund flow: Awaiting Receipt → Refunding → Refunded
5. Illegal transition: Completed → Refund application is prohibited (exception validation)
```

### Technique 5: Scenario Method
**Principle**: Simulate real-world user journeys and chain multi-step end-to-end scenarios.
```
Scenario construction formula:
  Basic Flow (main success scenario) + Alternative Flows (branch / exception scenarios)

Example- E-commerce order-placement scenario:
Basic Flow:
  Select product → Add to cart → Select shipping address → Select coupon → Submit order → Pay → Complete

Alternative-Flow List:
  AF1: Product out of stock (show sold-out prompt after product selection)
  AF2: No shipping address (prompt to add address upon submission)
  AF3: Coupon does not satisfy conditions (greyed out and non-selectable)
  AF4: Payment failure (redirect to payment-failure page with retry option)
  AF5: Payment timeout (order closed, return to product list)
  AF6: Network interruption (payment aborted, handle order status)
  AF7: Duplicate submission (anti-duplicate order validation)

Each alternative flow corresponds to one complete test case.
```

### Technique 6: Error Guessing
**Principle**: Infer high-probability defect-prone scenarios based on experience and intuition.
```
High-value error-guessing points:
【Data Layer】
- Null values: null / "" / " " (blank string) / undefined
- Special characters: ' " < > & ; # % @ \ / | * ?
- Over-length input: exceeds database field-length constraints
- Type confusion: passing string for numeric field, mal-formed date format
- Encoding issues: Chinese characters, emojis, special Unicode characters

【Business Layer】
- Duplicate operations: rapid double-click on submit button
- Concurrent operations: simultaneous deduction of inventory / points
- Cross-session operations: User A manipulates data belonging to User B
- State inconsistency: frontend display mismatches backend state

【System Layer】
- File upload: oversized files / 0-byte files / executable files
- Image processing: upload non-image files renamed with image extensions
- Time-zone issues: time calculation across time zones
- Precision issues: decimal-precision loss in monetary calculations
```

---
## Standard Test-Case Template
```markdown
### [TC-ModuleAbbrev-SeqNo]: [Case Title, verb + object + scenario]
| Field | Content |
|------|------|
| **Case ID** | TC-[MODULE]-[NNN] |
| **Case Title** | [Verb][Target Object][Condition / Scenario] |
| **Module** | [Module Name] |
| **Case Type** | Functional Test / API Test / Security Test / Performance Test |
| **Design Method** | Equivalence Partitioning / Boundary Value / Decision Table / State Transition / Scenario Method / Error Guessing |
| **Priority** | P0 / P1 / P2 / P3 |
| **Preconditions** | [Concrete, verifiable conditions that must be satisfied before execution] |

**Test Steps**:
1. [Step-1 action with target object and concrete operation]
2. [Step-2 action]
3. [Step-N action]

**Test Data**:
```
Field Name: Concrete Value (explain source or meaning of value)
```

**Expected Results**:
1. [Verifiable expected outcome; avoid vague wording such as "correct" or "success"]
2. [List multiple verification points item-by-item if applicable]
3. [Full validation covering UI display, database state and API responses]

**Notes**: [Associated requirement ID REQ-XXX / link to design document / special caveats]
```

---
## Hard Rules for Design Quality
❌ **Forbid** the following patterns (revise immediately if found):
- Expected results with non-verifiable descriptions such as "display correctly", "run normally", "succeeded"
- One case containing multiple unrelated verification points
- Non-quantified time wording in steps such as "wait for a moment", "later"
- Non-reproducible preconditions (e.g. "the user just performed some operation")
- Missing critical test data that renders the case non-executable on its own
```
