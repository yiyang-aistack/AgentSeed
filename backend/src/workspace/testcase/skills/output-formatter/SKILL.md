---
name: output-formatter
description: "Governs the final output format and specifications for test cases. Ensures all generated test cases comply with import-format requirements for enterprise-grade test management tools (Jira Xray, TestRail, ZenTao, TAPD). It also supports multiple output formats including Markdown, CSV/Excel, and JSON. Activate when users request formatted output or export of test cases."
---

# Test-Case Output Format Specification Skill
## Activation Scenarios
- Define output format before generating final test cases
- User requests export in a specific format (Excel / CSV / JSON / Markdown)
- Need to import test cases into test-management tools
- Need to re-format existing test cases

---
## Test-Case Naming Convention
```
Format: TC-[ProjectCode]-[ModuleAbbreviation]-[SequenceNumber]
ProjectCode: 2-4 uppercase letters (e.g. CRM / OMS / USER)
ModuleAbbreviation: 2-6 uppercase letters (see lookup table below for common abbreviations)
SequenceNumber: 3-digit numeric value starting from 001

Examples:
TC-CRM-LOGIN-001   → CRM project, Login module, Case #1
TC-OMS-ORDER-012   → OMS project, Order module, Case #12
TC-USER-AUTH-001   → User system, Authentication module, Case #1
```

**Common Module Abbreviation Lookup Table**:

| Business Module | Abbreviation | Business Module | Abbreviation |
|---|---|---|---|
| User Login | LOGIN | Permission Management | AUTH |
| User Registration | REG | Product Management | PROD |
| Personal Profile | PROFILE | Order Management | ORDER |
| Shopping Cart | CART | Payment & Settlement | PAY |
| Search Function | SEARCH | Message Notification | MSG |
| File Upload | UPLOAD | Data Export | EXPORT |
| System Settings | SYS | Report & Statistics | REPORT |

---
## Output Format 1: Standard Markdown Format (Default)
Use the following Markdown template for each individual test case:
```markdown
---
### TC-[PROJECT]-[MODULE]-[NNN]: [Test-Case Title]
> **Module**: [Module Name] ｜ **Priority**: [P0/P1/P2/P3] ｜ **Type**: [Case Type] ｜ **Method**: [Design Technique]

**Preconditions**:
- [Condition 1, concrete and verifiable]
- [Condition 2]

**Test Steps**:
| Step # | Action Description | Target Object |
|---|---|---|
| 1 | [Concrete action, use active verbs: Input / Click / Select / Upload] | [Target UI element or API] |
| 2 | [Concrete action] | [Target Object] |
| N | [Concrete action] | [Target Object] |

**Test Data**:
```
[Field Name]: [Concrete Value]     # [Explanation]
[Field Name]: [Concrete Value]
```

**Expected Results**:
1. ✅ **UI Layer**: Precise description of page / component state changes
2. ✅ **API Layer**: HTTP status codes, key fields within response payload
3. ✅ **Data Layer**: State changes in database / cache
4. ✅ **Log Layer**: Critical operation-log records (if applicable)

**Notes**: Linked Requirement `REQ-[ID]` | Risk Level: [High / Medium / Low]
```
---

## Output Format 2: Consolidated Table Format (Full-Module Overview)
After generating all test cases, provide a summary table for quick review:
```markdown
## Test-Case Summary Table
| Case ID | Case Title | Module | Priority | Type | Design Method | Preconditions | Expected-Result Summary |
|---|---|---|---|---|---|---|---|
| TC-XXX-LOGIN-001 | Login with valid username and password | User Login | P0 | Functional | Equivalence Partitioning | Account is registered | Redirect to homepage, username displayed |
| TC-XXX-LOGIN-002 | Login with incorrect password | User Login | P1 | Functional | Error Guessing | Account is registered | Prompt for wrong password, no page redirect |

**Statistics Summary**:
| Metric | Count |
|---|---|
| Total Cases | N |
| P0 Cases | N |
| P1 Cases | N |
| P2 Cases | N |
| P3 Cases | N |
| Functional Test | N |
| API Test | N |
| Security Test | N |
```

## Output Format 3: CSV Format (For Excel / Test-Tool Import)
```csv
CaseID,CaseTitle,Module,CaseType,Priority,Preconditions,TestSteps,TestData,ExpectedResults,Notes
TC-XXX-LOGIN-001,Login with valid username and password,User Login,Functional Test,P0,"Registered active account","1.Open login page;2.Input username;3.Input password;4.Click login","username:test001;password:Test@123","1.Redirect to homepage;2.Display username;3.Generate login log",REQ-LOGIN-001
```

## Output Format 4: JSON Format (Programmatic Consumption)
```json
{
  "test_suite": {
    "project": "[Project Name]",
    "module": "[Module Name]",
    "generated_at": "2024-01-01T00:00:00Z",
    "total_count": 1,
    "test_cases": [
      {
        "id": "TC-XXX-LOGIN-001",
        "title": "Successful login with valid account credentials",
        "module": "User Login",
        "type": "functional",
        "priority": "P0",
        "design_method": "equivalence_partitioning",
        "preconditions": ["Account is registered", "Account status is active"],
        "steps": [
          {"seq": 1, "action": "Open login page", "target": "Login-page URL"},
          {"seq": 2, "action": "Input username", "target": "Username input field", "data": "test001"}
        ],
        "test_data": {"username": "test001", "password": "Test@123"},
        "expected_results": [
          "HTTP 200 response containing token field",
          "Page redirect to /dashboard",
          "New record inserted into login_log database table"
        ],
        "requirements": ["REQ-LOGIN-001"],
        "risk_level": "high"
      }
    ]
  }
}
```

---
## Format Selection Guide

| Use-Case | Recommended Format |
|---|---|
| Human review within chat session | Detailed Markdown format |
| Quick full-scope overview | Markdown summary table |
| Import into ZenTao / TAPD / TestRail | CSV format |
| Import into Jira Xray | JSON format |
| Automated-script consumption | JSON format |

> 💡 **Default Behavior**: If no format is specified, output detailed Markdown format by default. Append the summary table after finishing each module.

