# Documentation Agent Testing Guide

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-08-11  

---

## 1. Purpose

This document defines the testing strategy, test coverage, execution
procedures, and acceptance testing guidance specific to the Project0
Documentation Agent.

The Documentation Agent follows the repository-wide testing principles
and conventions defined by `Testing_Guide.md`. This document supplements
that guide with Documentation Agent-specific unit, integration,
workflow, UI, reasoning-provider, repository-safety, and browser
acceptance testing.

The objective is to verify that the Documentation Agent performs
documentation work accurately, predictably, safely, and under human
control.

---

## 2. Objectives

Documentation Agent testing is intended to:

- Verify Documentation Agent-specific component behavior.
- Validate the complete documentation workflow.
- Confirm AI-generated proposals are correctly translated into controlled documentation operations.
- Verify preliminary and final validation behavior.
- Confirm human review decisions control repository modification.
- Ensure approved changes are applied correctly and unrelated content remains unchanged.
- Verify repository failures and invalid proposals fail safely.
- Validate Dashboard-hosted Documentation Agent interaction.
- Detect regressions in previously corrected workflow behavior.
- Provide confidence before declaring the Documentation Agent complete.

---

## 3. Testing Principles

Documentation Agent testing follows the general principles defined by `Testing_Guide.md` and additionally emphasizes:

- Test repository effects, not only returned workflow status.
- Verify that rejected and skipped proposals do not modify repository content.
- Verify that approved proposals modify only the intended content.
- Preserve realistic Markdown structure in repository-update tests.
- Exercise deterministic components independently of AI providers whenever practical.
- Use stub or fake reasoning providers for deterministic automated tests.
- Test real local AI-provider behavior separately from deterministic regression tests.
- Treat browser-based workflow testing as acceptance testing rather than a replacement for automated unit and integration tests.
- Add regression tests when exploratory or browser testing exposes a defect.

---

## 4. Test Organization

Documentation Agent-specific tests use the Project0 test organization defined by `Testing_Guide.md`.

Documentation Agent tests may be located in agent-specific directories or alongside shared Project0 components when the test verifies Documentation Agent-specific use of those components.

Relevant locations include:

```text
tests/
├── unit/
│   ├── agents/
│   │   └── documentation/
│   ├── models/
│   ├── reasoning/
│   ├── repository/
│   ├── validation/
│   └── workflow/
│
├── integration/
│   ├── agents/
│   │   └── documentation/
│   └── platform/
│
└── acceptance/
    └── agents/
        └── documentation/
```

Documentation Agent acceptance tests are maintained separately from unit and integration tests under `tests/acceptance/agents/documentation/`.

Acceptance tests verify Documentation Agent behavior through the actual browser/UI boundary. They should interact with the Dashboard-hosted Documentation Agent as a user would, rather than calling Project0 Python APIs such as the platform dispatcher or Documentation Workflow directly.

High-level workflow tests that assemble real Project0 services but enter through Python APIs belong under `tests/integration/agents/documentation/`.

### 4.1 Verification Scenario and Test Naming

Documentation Agent verification scenario identifiers describe the behavior being verified and do not identify a testing layer.

Examples:

```text
DA-FUN-001
DA-SAF-001
DA-AI-001
```

Automated tests that provide evidence for a scenario add a testing-layer prefix to the test function name:

```text
test_INT_DA_FUN_001_documentation_request_processing
test_UI_DA_FUN_001_documentation_request_processing
```

The supported layer prefixes are:

- `INT` — integration tests that exercise assembled Project0 and Documentation Agent components through Python/service boundaries.
- `UI` — browser acceptance tests that exercise the Documentation Agent through the Dashboard/UI boundary.

This convention allows one verification scenario to receive evidence from more than one testing layer without creating duplicate scenario identifiers.

---

## 5. Documentation Agent Test Coverage

Current Documentation Agent testing includes the following areas.

### 5.1 Documentation Agent UI

Tests verify:

- Ready-page creation.
- Documentation request validation and normalization.
- Mapping workflow results into Documentation Agent view models.
- Proposal and validation presentation.
- Repository difference generation.
- Focused difference presentation.
- Insert-after difference behavior.
- Surgical anchored difference behavior.
- Multiple difference hunks.
- Completed workflow presentation.
- Completed-with-warning presentation.
- Preliminary validation failure presentation.
- Explicit workflow failure presentation.
- Workflow exception handling.
- Review-decision normalization and result mapping.
- Safe handling of unknown mapped values.

### 5.2 Documentation Workflow

Documentation Agent workflow tests verify the agent-specific coordination of reusable Project0 services and Documentation Agent workflow components, including:

- Knowledge Service.
- Reasoning Service.
- Validation Service.
- Review Coordinator.
- Repository Update Service.
- Git Diff Service.

These tests verify that the Documentation Agent composes the required services correctly to perform its documentation workflow.

Generic correctness of reusable Project0 services remains covered by the Project0-wide `Testing_Guide.md`.

Documentation Agent workflow tests should verify both structured workflow results and repository effects where applicable.

### 5.3 Review Decisions

Tests should verify each supported human review decision:

- Approve.
- Revise.
- Reject.
- Skip.

Approval shall be the only review path that permits the applicable
repository change to be applied.

### 5.4 Repository Update Behavior

Tests verify controlled documentation modification, including:

- Approved Markdown updates.
- Anchored insert behavior.
- Anchored replacement behavior.
- Preservation of anchor content when required.
- Preservation of unrelated document content.
- Repository path safety.
- Failure behavior when a requested update cannot be applied reliably.

### 5.5 Validation

Documentation Agent testing verifies:

- Preliminary validation before approval.
- Final validation after approved repository changes.
- Markdown validation.
- Link validation.
- MkDocs validation.
- Documentation consistency validation.
- Proper workflow handling when validation fails.

### 5.6 Documentation Reasoning Behavior

Documentation Agent reasoning tests verify agent-specific reasoning behavior, including:

- Construction of documentation-specific prompts.
- Inclusion of appropriate repository and documentation context.
- Conversion of reasoning results into Documentation Agent proposals.
- Documentation edit intent such as insert and replace behavior.
- Selection and preservation of appropriate anchors.
- Safe handling of invalid, incomplete, or unsupported reasoning output.

Generic Reasoning Service behavior, provider abstraction, and provider-independent reasoning infrastructure are tested according to `Testing_Guide.md`.

Real AI-provider behavior should be evaluated separately from deterministic automated tests because model output may vary.

### 5.7 Dashboard Integration

Tests verify:

- Documentation Agent routes integrate with the Dashboard Framework.
- Documentation Agent content renders inside the Dashboard Work Area.
- Dashboard ownership of the shared application shell and navigation is preserved.
- Documentation Agent workflow interaction does not require a separate application shell.

### 5.8 End-to-End Workflow

Integration testing should exercise the complete path:

``` text
Documentation Request
        ↓
Platform Dispatcher
        ↓
Documentation Workflow
        ↓
Knowledge / Context
        ↓
Reasoning
        ↓
Preliminary Validation
        ↓
Human Review Decision
        ↓
Repository Update
        ↓
Final Validation
        ↓
Git Diff
        ↓
Workflow Result
```

---

## 6. Running Documentation Agent Tests

All commands assume the current working directory is the Project0
repository root.

### 6.1 Documentation Agent UI Unit Tests

``` bash
python -m pytest tests/unit/agents/documentation/test_documentation_agent_ui_service.py -v
```

Run other Documentation Agent unit test modules in the same directory as
applicable.

### 6.2 Documentation Workflow Unit Tests

``` bash
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
python -m pytest tests/unit/workflow/test_documentation_workflow.py -v
```

### 6.3 Repository Update and Git Diff Tests

``` bash
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
```

### 6.4 Documentation Workflow Models

``` bash
python -m pytest tests/unit/models/test_documentation_workflow_models.py -v
```

### 6.5 Documentation Reasoning Tests

Run Documentation Agent-specific prompt, proposal, and reasoning-integration tests applicable to the change being validated.

Generic Reasoning Service and provider infrastructure tests are defined by `Testing_Guide.md` and are exercised again by the complete Project0 regression suite.

Provider-specific Documentation Agent behavior should also be evaluated when validating a configured reasoning provider.

### 6.6 Documentation Validation Tests

Run tests that verify Documentation Agent-specific use of preliminary validation, final validation, and documentation validators applicable to the workflow being changed.

Documentation Agent testing should verify that:

- Preliminary validation occurs before approval where required.
- Validation results are correctly represented in the review workflow.
- Final validation occurs after approved repository modification.
- Validation failures produce the appropriate Documentation Agent workflow state.

Generic Validation Service infrastructure is tested according to `Testing_Guide.md` and is exercised again by the complete Project0 regression suite.

### 6.7 Integration Tests

Run Documentation Agent-specific integration tests:

```bash
python -m pytest tests/integration/agents/documentation/test_documentation_workflow_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_agent_ui_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/documentation -v
```

The `test_documentation_agent_end_to_end_flow.py` module contains high-level Documentation Agent workflow scenarios that exercise real Project0 service composition through Python APIs. These scenarios are integration tests because they enter through the platform/workflow API boundary rather than through a browser.

Scenario-oriented test functions in this module use the `INT` layer prefix, for example:

```text
test_INT_DA_FUN_001_documentation_request_processing
```

Additional Documentation Agent integration modules should be included as they are added.

Documentation Agent integration with the Dashboard Framework should be verified through agent-specific integration scenarios. Project0-wide Dashboard Framework integration testing is governed by `Testing_Guide.md`.

### 6.8 Documentation Agent Acceptance Tests

Documentation Agent acceptance tests belong under:

```text
tests/acceptance/agents/documentation/
```

Acceptance tests shall verify Documentation Agent behavior through the actual Dashboard/browser boundary.

The intended acceptance automation tool is Playwright for Python with pytest. Initial automated browser coverage should use Chromium only.

Scenario-oriented Playwright test functions shall use the `UI` layer prefix, for example:

```text
test_UI_DA_FUN_001_documentation_request_processing
```

Acceptance automation should be introduced incrementally. Initial scenarios should verify:

- Documentation Agent page renders.
- Documentation request field is available.
- Target documentation path field is available.
- Submit Documentation Request button is available.
- Request submission produces the visible Processing state.
- Review/proposal UI is presented.
- Reject workflow operates correctly.
- Approve workflow operates correctly.
- Repository effects are verified where applicable.

Playwright automatic waiting should be preferred over arbitrary sleep calls because local reasoning execution time may vary.

The acceptance suite is distinct from unit and integration testing:

- Unit tests verify individual component behavior.
- Integration tests verify cooperation between assembled Project0 and Documentation Agent components.
- Acceptance tests verify that a real user can successfully operate the Documentation Agent through the browser/UI boundary.

Acceptance scenarios that are not yet automated shall not be treated as passed acceptance requirements.

### 6.9 Complete Project0 Regression Test

After Documentation Agent-specific tests pass, run the complete Project0 suite:

```bash
python -m pytest
```

This final regression run verifies that Documentation Agent changes have not introduced regressions into shared Project0 platform services, the Dashboard Framework, other agents, or integration workflows.

The complete Project0 regression suite is governed by `Testing_Guide.md`.

---

## 7. Browser Acceptance and Exploratory AI Testing

Automated unit and integration tests are necessary but do not fully evaluate the user-visible workflow or the quality of AI-generated documentation proposals.

Browser acceptance testing should therefore verify the user workflow through the actual Dashboard-hosted Documentation Agent interface.

Exploratory AI testing should remain a separate qualitative activity because real Ollama/qwen2.5:7b output may vary and may require human judgment for factual grounding, proposal quality, hallucination detection, rationale usefulness, and appropriateness of edits.

Representative browser and exploratory scenarios include:

- Insert a new bullet beneath an existing section or anchor.
- Replace an existing sentence.
- Update an existing paragraph.
- Add content beneath a Markdown heading.
- Exercise multiple target documentation paths.
- Review a proposal before approval.
- Approve a proposal and verify the repository result.
- Reject a proposal and verify no repository change.
- Skip a proposal and verify no repository change.
- Revise a proposal and verify regenerated output.
- Exercise preliminary validation failure.
- Exercise final validation behavior.
- Verify the final Git diff.
- Verify completion status and workflow summary.
- Verify that unrelated files remain unchanged.

Observed browser behavior should be compared with the actual repository
content. Presentation artifacts shall not be assumed to represent
repository corruption without verifying the resulting file content.

---

## 8. Local AI Provider Testing

The Documentation Agent may use a local AI reasoning provider through
the Project0 Reasoning Service.

Local-provider testing should verify:

- Provider configuration is loaded correctly.
- The configured model can be reached.
- Prompt construction includes the required repository context and user request.
- Reasoning results are converted into valid Documentation Agent proposals.
- Edit intent is interpreted correctly.
- Anchors are sufficiently precise for controlled repository updates.
- Invalid or incomplete AI output fails safely.
- Repository modification remains subject to validation and human approval regardless of model output.

Because model responses may vary, local-provider testing is primarily
behavioral and exploratory. Deterministic unit tests should continue to
use controlled providers or fixtures where practical.

---

## 9. Repository Safety Acceptance Tests

Before declaring the Documentation Agent complete, verify that:

- Only approved files are modified.
- Only approved content is applied.
- Rejected proposals leave repository content unchanged.
- Skipped proposals leave repository content unchanged.
- Missing anchors fail safely.
- Ambiguous anchors fail safely where deterministic application cannot be established.
- Invalid repository paths are rejected.
- Paths outside the configured repository root cannot be modified.
- Unrelated files remain unchanged.
- Validation failure does not result in an inappropriate successful completion state.
- Final Git diff accurately reflects applied changes.

Repository safety failures are release-blocking defects.

---

## 10. Documentation Agent Completion Criteria

The Documentation Agent may be considered complete for its current
version when:

- Documentation Agent unit tests pass.
- Documentation workflow integration tests pass.
- Required Documentation Agent acceptance scenarios pass.
- Documentation Agent integration with the Dashboard Framework has been verified.
- Complete Project0 regression tests pass.
- Representative insert and replace operations have been verified.
- Approve, revise, reject, and skip behavior has been verified.
- Repository safety scenarios have been verified.
- Preliminary and final validation behavior has been verified.
- Real local reasoning-provider behavior has been exercised with varied documentation requests.
- Browser-based review and completion workflows are usable.
- Known non-critical presentation issues are documented separately from functional defects.
- No known defect permits unauthorized or unintended repository modification.
- Documentation accurately reflects the validated system behavior.

---

## 11. Regression Testing

When a Documentation Agent defect is discovered:

1. Reproduce the defect in the smallest practical environment.
2. Determine whether the defect belongs to reasoning, workflow, repository update, validation, or presentation behavior.
3. Add or update a focused automated test when the behavior can be tested deterministically.
4. Implement the correction.
5. Run the focused test.
6. Run the applicable component test suite.
7. Run Documentation Agent integration tests.
8. Run applicable Documentation Agent acceptance tests.
9. Run the complete Project0 regression suite.
10. Repeat the relevant browser or local-provider scenario when applicable.

Previously corrected defects should remain represented by regression
tests whenever practical.

---

## 12. Current Validation Baseline

At the time of this update, the Documentation Agent-specific validation baseline includes:

- Documentation Agent UI unit tests passing.
- Documentation workflow unit tests passing.
- Documentation Agent workflow integration tests passing.
- High-level Documentation Agent end-to-end workflow integration scenarios passing.
- Documentation Agent integration with the Dashboard Work Area verified.
- Human review workflow behavior exercised.
- Controlled repository update behavior verified.
- Preliminary and final validation behavior verified.
- Local reasoning-provider behavior exercised through Documentation Agent workflows.
- Seven implemented high-level workflow scenarios passing as integration tests; seven additional scenarios remain explicitly skipped/deferred.
- Playwright-based browser acceptance automation not yet established.
- Complete Project0 regression baseline: 647 passed, 7 skipped.

The complete Project0 regression suite must also pass before Documentation Agent changes are committed.

Project0-wide test counts, Dashboard Framework validation status, and shared platform testing requirements are governed by `Testing_Guide.md` and should not be duplicated in this document.

---

## 13. Future Testing Enhancements

Future Documentation Agent testing may include:

- Playwright-based browser acceptance testing.
- Expanded automated browser coverage.
- Additional multi-document workflow scenarios.
- Automated repository integrity fixtures.
- AI-provider evaluation datasets.
- Proposal-quality scoring.
- Additional revision-workflow tests.
- Performance testing for larger documentation repositories.
- Continuous Integration execution of Documentation Agent regression suites.
- Automated acceptance-test reporting.

---

## 14. Summary

Documentation Agent testing verifies the behavior required to demonstrate that the agent performs AI-assisted documentation work accurately, safely, predictably, and under human control.

This includes documentation-specific reasoning, proposal generation, review decisions, controlled repository modification, preliminary and final validation, repository safety, Dashboard-hosted interaction, and end-to-end Documentation Agent workflow behavior.

Project0-wide testing principles, shared service correctness, Dashboard Framework testing, and complete repository regression testing remain governed by `Testing_Guide.md`.

Together, the Project0 Testing Guide and Documentation Agent Testing Guide provide complementary validation without duplicating ownership of platform and agent testing responsibilities.
