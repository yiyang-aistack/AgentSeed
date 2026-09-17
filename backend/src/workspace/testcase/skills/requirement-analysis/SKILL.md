---
name: requirement-analysis
description: "Activate this Skill immediately when users provide requirement documents, product PRDs, user stories, functional descriptions, or any form of test-requirement inputs. It conducts systematic in-depth analysis of requirements, extracts test points, builds a function matrix, identifies risk areas, and lays a solid foundation for subsequent test design."
---

# Requirement In-Depth Analysis Skill
## Activation Scenarios
- Users upload or paste requirement documents (PDF, Word, Markdown, plain text)
- Users describe product functions or business processes
- Users provide User Stories or Acceptance Criteria (AC)
- Users request analysis of the test scope for a specific module

## Execution Workflow
### Step 1: Document Structure Parsing
First, structurally decompose the input document and identify:
- **Document Type**: PRD / API Document / User Story / Design Specification / Verbal Requirement
- **List of Functional Modules**: Grouped by business domain (e.g. authentication module, order module, payment module)
- **Core Business Processes**: Main process + branch processes + exception processes
- **Input & Output Definitions**: Interface parameters, UI fields, data formats
- **Business Rules**: Constraints, calculation logic, state-machine rules

### Step 2: Test-Point Extraction Framework (INVEST Principle)
Extract test points for each functional feature using the dimensions below:

| Dimension | Extracted Content | Example |
|---|---|---|
| **Functionality** | Whether core features work as expected | Jump to homepage upon successful login |
| **Data** | Type, range and format of input data | 11-digit mobile phone number |
| **Rules** | Business constraints and calculation logic | Coupons cannot be stacked |
| **State** | Object state changes and transitions | Order status: Pending Payment → Paid |
| **Interaction** | Component linkage and dependencies | Three-level linkage for province-city-district selection |
| **Permission** | Access control for different roles | Administrators may delete records; regular users may not |
| **Exception** | Handling strategies for error scenarios | Prompt retry on network timeout |
| **Performance** | Response time, concurrency, data volume | List page loading within 2 seconds |

### Step 3: Build Function Matrix
Output a standard function-matrix table:
```
## Function Test Matrix
| Module | Feature Point | Test Point | Priority | Risk Level | Test Type |
|---|---|---|---|---|---|
| User Authentication | Mobile-phone Login | Verification code valid for 5 minutes | P0 | High | Functional + Security |
| User Authentication | Third-party Login | WeChat / Alipay OAuth | P1 | Medium | Functional + Compatibility |
```

### Step 4: Risk Identification & Labeling
Highlight these high-risk areas:
- 🔴 **Security Risk**: Authentication, authorization, data encryption, SQL-injection vectors, XSS
- 🟠 **Data-Integrity Risk**: Transaction processing, concurrent writes, data consistency
- 🟡 **Compatibility Risk**: Multi-client adaptation, browser discrepancies, API-version compatibility
- 🔵 **Performance Risk**: High-frequency interfaces, large-data-volume operations, file uploads
- ⚪ **Business-Logic Risk**: Complex calculations, multi-condition judgements, state machines

### Step 5: Test-Scope Statement
Generate the test-scope statement:
```
## Test-Scope Statement
### In Scope
- [List all functional modules included for testing]
### Out of Scope
- [Specify items excluded from the current test cycle]
### Test Assumptions & Preconditions
- [List environment, test data and permission assumptions for test execution]
### Dependencies
- [List dependencies with other modules or external systems]
```

## Output Specifications
After finishing analysis, output the following contents **in this exact order**:
1. **📊 Requirement-Analysis Summary**: Document type, count of functional modules, count of core business processes
2. **📋 Function Test Matrix**: Complete matrix of features versus test dimensions
3. **⚠️ Risk List**: Risk items sorted by risk level
4. **📐 Test-Scope Statement**: In-scope / out-of-scope items plus assumptions
5. **📈 Estimated Test-Case Count**: Estimated case count per module and total case count

## Key Reminders
> ⚡ **Mandatory Rule**: Requirement analysis must be completed **before generating any test cases**. Analysis results directly govern test-strategy selection and test-case quality.
>
> 🎯 **Depth Requirement**: Go beyond explicit feature descriptions. Uncover implicit requirements (e.g. security-log records after login success), negative-path requirements (e.g. account lockout after 5 wrong-password attempts), and quality requirements (e.g. response-time criteria).
>
> 🔍 Handling Open Questions: If requirements are ambiguous, contradictory or incomplete, mark **Items to Be Clarified** in the analysis report and raise concrete questions for stakeholder confirmation.