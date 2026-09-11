# Testing Guide

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

This guide defines Project0's implemented test organization, ownership boundaries, environment requirements, execution commands, result-reporting rules, and standards for adding tests.

Project0 uses unit, integration, and acceptance testing. Test-source presence shows intended coverage only; it does not establish that a test was collected, executed, or passed. Current execution evidence belongs in [Project0 Test Results](../platform/Project0_Test_Results.md).

## 2. Testing Objectives

Project0 testing is intended to:

- verify individual component behavior;
- validate collaboration between production components;
- confirm externally observable Dashboard and agent behavior;
- detect regressions during incremental development;
- support safe refactoring;
- validate error, state, review, and safety contracts;
- preserve deterministic behavior outside live-provider checks; and
- provide commit-specific evidence before completion or release claims.

## 3. Testing Principles

- Test observable behavior and contracts rather than incidental implementation details.
- Keep default regression tests deterministic and repeatable.
- Use dependency injection and contract-correct stubs or fakes to isolate external systems.
- Avoid live network, model, credential, and mutable external-state dependencies in the default regression path.
- Test one coherent responsibility per test.
- Prefer focused tests that fail at the closest meaningful boundary.
- Keep tests isolated from the developer's real repository content, credentials, and previous runs.
- Use temporary directories and explicit fixtures for filesystem behavior.
- Do not use arbitrary sleep delays for synchronization or acceptance criteria.
- Preserve a clear distinction between platform-owned and agent-owned verification.
- Report what actually ran; never infer success from files, past counts, or a different commit.

## 4. Repository Test Layout

```text
tests/
├── unit/
│   ├── agents/
│   ├── artifacts/
│   ├── common/
│   ├── config/
│   ├── dashboard/
│   ├── knowledge/
│   ├── models/
│   ├── platform/
│   ├── reasoning/
│   ├── repository/
│   ├── skills/
│   ├── validation/
│   └── workflow/
├── integration/
│   ├── agents/
│   └── platform/
├── acceptance/
│   ├── agents/
│   └── platform/
└── test_data/
```

The current repository uses `tests/test_data/`; it does not contain the `tests/resources/` directory shown in the older guide.

## 5. Test Layers and Ownership

### 5.1 Unit Tests

Unit tests exercise one service, model, provider adapter, route, UI service, registry, validator, or workflow coordinator with isolated collaborators.

Typical characteristics:

- deterministic and fast;
- no required live network or model;
- focused inputs and assertions;
- temporary or in-memory state; and
- direct verification of success, warning, error, and edge cases.

### 5.2 Integration Tests

Integration tests combine multiple production components across a real application or service boundary.

Platform integration coverage includes repository/context, knowledge, dispatcher, reasoning, validation, Ollama request construction, and Dashboard flows. Agent integration suites validate each agent's use of shared services and remain owned by the corresponding agent documentation.

Integration tests should use real internal collaborators where practical while replacing external or nondeterministic services at a defined boundary.

### 5.3 Acceptance Tests

Acceptance tests verify externally observable behavior through the intended user boundary. Current non-empty acceptance modules use browser automation for the Documentation and Research agent interfaces.

These tests:

- import Playwright;
- rely on pytest browser fixtures;
- target a separately running Dashboard at `http://127.0.0.1:8001`; and
- exercise request, review, results, and end-to-end UI scenarios.

`tests/acceptance/platform/test_ollama_acceptance.py` exists but is empty and provides no executable acceptance coverage.

Acceptance testing complements rather than replaces unit and integration testing.

### 5.4 Live Validation

Live Ollama or research-source checks validate a particular external environment. They are not substitutes for deterministic regression and should not run implicitly as part of a reproducible default suite unless their prerequisites, isolation, markers, and result interpretation are formally defined.

## 6. Test Dependencies and Environment

Install Project0 and its declared test extra from the repository root:

```bash
python -m pip install -e '.[test]'
```

The `test` extra declares pytest and httpx. Runtime dependencies are installed through the base package.

Browser acceptance requires additional Playwright tooling and installed browser binaries. Neither Playwright nor its pytest integration is declared in the current `pyproject.toml`, so a clean `.[test]` installation is insufficient for browser-test collection and execution.

At the pinned commit:

- `pyproject.toml` contains no pytest-specific configuration section;
- there is no `pytest.ini`, `setup.cfg`, or `tox.ini` supplying pytest configuration; and
- no `.github/workflows/` continuous-integration definition is checked in.

All commands in this guide assume the repository root as the current working directory and the intended Python environment is active.

## 7. Standard Test Commands

### 7.1 Complete Regression

```bash
python -m pytest
```

This collects all applicable unit, integration, and acceptance tests. Because browser modules import Playwright and target a running Dashboard, the complete command requires the browser environment and Dashboard procedure described below.

### 7.2 Test Layers

```bash
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/acceptance -v
```

### 7.3 Reusable Platform Unit Suites

```bash
python -m pytest tests/unit/artifacts -v
python -m pytest tests/unit/common -v
python -m pytest tests/unit/config -v
python -m pytest tests/unit/dashboard -v
python -m pytest tests/unit/knowledge -v
python -m pytest tests/unit/models -v
python -m pytest tests/unit/platform -v
python -m pytest tests/unit/reasoning -v
python -m pytest tests/unit/repository -v
python -m pytest tests/unit/skills -v
python -m pytest tests/unit/validation -v
```

Generic workflow and shared review-coordinator units:

```bash
python -m pytest tests/unit/workflow/test_workflow_engine.py -v
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
```

The Documentation and Research workflow modules under `tests/unit/workflow/` are agent-specific even though they reside in the shared workflow test directory.

### 7.4 Platform Integration Suites

```bash
python -m pytest tests/integration/platform/test_core_platform_flow.py -v
python -m pytest tests/integration/platform/test_context_builder_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
python -m pytest tests/integration/platform/test_knowledge_service_flow.py -v
python -m pytest tests/integration/platform/test_reasoning_service_flow.py -v
python -m pytest tests/integration/platform/test_ollama_reasoning_flow.py -v
python -m pytest tests/integration/platform/test_validation_service_flow.py -v
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
```

Run the complete platform integration directory with:

```bash
python -m pytest tests/integration/platform -v
```

### 7.5 Agent Suites

```bash
python -m pytest tests/unit/agents/documentation -v
python -m pytest tests/integration/agents/documentation -v
python -m pytest tests/acceptance/agents/documentation -v

python -m pytest tests/unit/agents/research -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
```

The agent testing guides contain the detailed scenarios, focused files, provider bounds, and acceptance criteria:

- [Documentation Agent Testing Guide](../agents/documentation/Documentation_Agent_Testing_Guide.md)
- [Research Agent Testing Guide](../agents/research/Research_Agent_Testing_Guide.md)

`TEST_COMMANDS.md` at the repository root is the concise command reference.

## 8. Browser Acceptance Procedure

Provision Playwright, its pytest fixtures, and required browser binaries in the test environment before collecting browser modules.

Use deterministic providers unless a test explicitly targets live behavior.

Terminal 1:

```bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
```

Confirm that the Dashboard is available at `http://127.0.0.1:8001`.

Terminal 2:

```bash
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/acceptance/agents/research -v
```

The acceptance suite does not start the Dashboard itself. The executable Dashboard factory must be used so both agent interfaces are registered.

### Visible Browser and Slow Motion

```bash
python -m pytest \
  tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py \
  -v -s --headed --ui-slowmo=750
```

`tests/acceptance/conftest.py` defines `--ui-slowmo=<milliseconds>`, defaults it to `0`, and rejects negative values. Slow motion is an observation aid only; tests must rely on Playwright synchronization and assertions rather than the delay.

## 9. Frequently Used Pytest Options

Verbose output:

```bash
python -m pytest -v
```

Stop after the first failure:

```bash
python -m pytest -x
```

Show the slowest tests:

```bash
python -m pytest --durations=10
```

Run one file:

```bash
python -m pytest path/to/test_file.py -v
```

Run one test function:

```bash
python -m pytest path/to/test_file.py::test_name -v
```

Show captured output while running:

```bash
python -m pytest -v -s
```

Browser options such as `--headed` require the externally provisioned Playwright pytest integration.

## 10. Deterministic Versus Live Behavior

- Ollama unit and integration tests replace or intercept HTTP behavior; they verify request/response handling, not availability of a local Ollama service or model.
- Research source-provider tests use controlled responses or fakes; they do not prove that public APIs are reachable at test time.
- Browser acceptance requires a real local Dashboard process but should use deterministic stub reasoning and source providers.
- Credentials and real API keys must not be embedded in tests, fixtures, logs, or recorded outputs.
- Provider-specific live checks should be run and reported separately with their exact environment, model/provider configuration, date, and scope.

## 11. Additional Integrity and Documentation Checks

Pytest does not replace source or documentation validation. Useful repository checks include:

```bash
python -m compileall -q src
mkdocs build --strict
```

When documentation or controlled Markdown update behavior changes, also run the relevant Markdown, Link, MkDocs, and Documentation Consistency validator tests.

At commit `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`, `python -m compileall -q src` fails because `src/project0/interfaces/knowledge_interfaces.py` begins and ends with Markdown code fences. This is a source-integrity failure, not a pytest result or test-environment problem.

## 12. Adding or Updating Tests

For each material production change:

1. identify the ownership boundary and observable behavior;
2. add or update the closest focused unit tests;
3. add integration coverage when production components interact;
4. add browser acceptance coverage for material user-visible behavior;
5. cover success, warning, failure, validation, and edge paths as applicable;
6. run focused tests during implementation;
7. run affected layer suites;
8. run source and documentation checks where applicable;
9. run the complete regression in a supported environment; and
10. commit production code, tests, and directly affected documentation together when practical.

Do not add an empty test file as evidence of coverage. A placeholder must be clearly identified as such or omitted until it contains executable tests.

### Fixture and Stub Guidance

- Reuse shared fixtures only when they express a genuinely shared contract.
- Keep fixture data minimal, explicit, and non-sensitive.
- Use temporary repository roots for read/write tests.
- Make stub responses conform to the real typed/provider contract.
- Assert that the expected dependency boundary was called when interaction is part of the behavior.
- Avoid mocks that merely reproduce implementation internals without proving an external effect.

## 13. Test Naming Conventions

Test files use:

```text
test_<component>.py
```

Ordinary test functions use descriptive behavior names:

```text
test_<expected_behavior>()
```

Examples:

```text
test_repository_reads_markdown()
test_missing_file_returns_error()
```

Test names should describe observable behavior, condition, and expected result where useful.

For test-plan scenarios verified at multiple layers, preserve the plan's scenario identifier and add the layer prefix:

```text
test_INT_<scenario_id>_<expected_behavior>()
test_UI_<scenario_id>_<expected_behavior>()
```

`INT` identifies assembled Python/service integration; `UI` identifies browser verification through the real application boundary. Scenario identifiers such as `DA-FUN-001` remain owned by the applicable agent test plan.

## 14. Result Interpretation and Reporting

A valid test record must identify:

- the exact commit or source state;
- date and environment;
- command and scope;
- pass, fail, error, and skip counts;
- relevant provider/model mode;
- browser or external-service prerequisites;
- excluded live checks; and
- separate source-compilation and documentation-build results.

Do not:

- carry a pass count forward after source changes;
- call an unavailable or unexecuted check passed;
- treat collection as execution;
- treat skipped tests as passed coverage;
- treat a unit/provider stub test as live-provider validation; or
- report test-file inventory as a regression result.

`docs/platform/Project0_Test_Results.md` is manually maintained. The Dashboard parses its bold `Tests` and `Validation` fields for display; it does not run or independently verify the suite.

At the pinned audit commit, pytest and MkDocs were unavailable in the audit environment, so no current pytest count or strict documentation-build result was established. The historical `1265 passed, 11 skipped` record from 2026-09-09 was not tied to the pinned commit and remains historical only.

## 15. Current Test Gaps

- Browser-test packages and browser-installation steps are not declared in project metadata.
- No checked-in CI workflow executes regression or documentation validation.
- `tests/acceptance/platform/test_ollama_acceptance.py` is empty.
- `tests/unit/models/test_skill_models.py` is empty.
- The source-compilation defect described above prevents a clean integrity result.
- The current pinned-commit pytest and strict MkDocs status is not established.

## 16. Completion Criteria

A repository-wide change is considered test-validated only when:

- focused tests for the changed behavior pass;
- affected unit, integration, and acceptance suites pass;
- the complete applicable regression passes in a supported environment;
- source compilation and documentation validation pass where applicable;
- unexpected warnings, errors, and collection failures are resolved;
- skips and excluded live tests are understood and recorded; and
- results are tied to the exact validated source state.

Agent-specific requirements can add stricter criteria but cannot replace shared platform validation for affected shared services.

## 17. Future Improvements

Potential future work, not current capability:

- declare and automate the Playwright browser-test environment;
- add checked-in continuous integration;
- add coverage measurement and thresholds;
- add formatter, linter, and static type-checking gates;
- add dependency and security scanning;
- define opt-in live-provider test markers and prerequisites;
- add performance and benchmark testing; and
- publish automated repository-health results.
