# Testing Guide

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-08-11

---

## 1. Purpose

This document describes the testing strategy used throughout the Project0 platform and provides the standard procedures for executing, extending, and maintaining the automated test suite.

Project0 emphasizes deterministic, repeatable testing. Every production component should include corresponding automated tests that execute without requiring external services, AI providers, or network connectivity whenever practical.

---

## 2. Objectives

The Project0 testing strategy is intended to:

* Verify correctness of individual components.
* Detect regressions during ongoing development.
* Support safe refactoring.
* Validate component interactions.
* Ensure deterministic platform behavior.
* Provide confidence before Git commits and releases.

---

## 3. Testing Philosophy

Project0 follows several fundamental testing principles.

* Test behavior rather than implementation details.
* Keep tests deterministic and repeatable.
* Avoid unnecessary mocking whenever practical.
* Use dependency injection to simplify testing.
* Test one responsibility per test.
* Prefer many focused tests over fewer complex tests.
* Execute quickly enough to encourage frequent use.
* Maintain complete isolation between tests.

---

## 4. Test Organization

The repository organizes automated tests into three primary categories.

```text
tests/
├── unit/
│
├── integration/
│
├── acceptance/
│
└── resources/
```

### 4.1 Unit Tests

Unit tests verify the behavior of a single component in isolation.

Typical characteristics include:

* Single class or module
* Deterministic execution
* No external dependencies
* Fast execution
* Focused assertions

### 4.2 Integration Tests

Integration tests verify interaction between multiple production components.

Typical characteristics include:

* Multiple collaborating components
* Real production implementations
* Minimal mocking
* Workflow validation
* End-to-end execution of platform services

### 4.3 Acceptance Tests

Acceptance tests verify externally observable system behavior through the same boundary used by the intended user.

Typical characteristics include:

* User-visible workflow verification
* Execution through the actual application boundary
* Browser/UI automation for Dashboard-hosted agents
* Validation of externally meaningful behavior
* Separation from direct Python/service API integration testing

Acceptance testing complements rather than replaces unit and integration testing.

---

## 5. Current Test Coverage

Current Project0 platform test categories include:

- Common
- Configuration
- Platform Dispatcher
- Workflow Engine
- Repository Services
- Knowledge Services
- Reasoning Services
- Validation Services
- Shared Models
- Dashboard Framework
- Platform Integration Workflows

This guide defines testing for reusable Project0 platform components and the Dashboard Framework.

Agent-specific behavior, workflows, acceptance criteria, integration scenarios, and browser/UI acceptance scenarios are documented in the applicable `<Agent>_Testing_Guide.md`.

Shared Project0 services may also be exercised by agent integration tests. Those agent-level tests verify the agent's use of the shared service and do not replace the platform-level tests defined by this guide.

As additional reusable platform services are implemented, corresponding test suites should be added.

---

## 6. Running Tests

All commands assume the current working directory is the Project0 repository root.

---

### 6.1 Unit Tests

### Repository

Repository tests in this guide verify reusable Project0 repository infrastructure. Agent-specific tests may exercise these services as dependencies but should document agent-specific repository behavior in the applicable Agent Testing Guide.

```bash
python -m pytest tests/unit/repository/test_repository_service.py -v
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
```

### Configuration

```bash
python -m pytest tests/unit/config/test_settings.py -v
```

### Common

```bash
python -m pytest tests/unit/common/test_logging_config.py -v
python -m pytest tests/unit/common/test_startup_validation.py -v
```

### Workflow

```bash
python -m pytest tests/unit/workflow/test_workflow_engine.py -v
```

### Knowledge

```bash
python -m pytest tests/unit/knowledge/test_context_builder.py -v
python -m pytest tests/unit/knowledge/test_context_filters.py -v
python -m pytest tests/unit/knowledge/test_context_rules.py -v
python -m pytest tests/unit/knowledge/test_document_parser.py -v
python -m pytest tests/unit/knowledge/test_document_index.py -v
python -m pytest tests/unit/knowledge/test_document_selector.py -v
python -m pytest tests/unit/knowledge/test_knowledge_service.py -v
python -m pytest tests/unit/knowledge/test_context_formatter.py -v
```

### Platform

```bash
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
```

### Dashboard

```bash
python -m pytest tests/unit/dashboard/test_dashboard_app.py -v
python -m pytest tests/unit/dashboard/test_dashboard_routes.py -v
```

### Models

```bash
python -m pytest tests/unit/models/test_context_models.py -v
python -m pytest tests/unit/models/test_workflow_models.py -v
python -m pytest tests/unit/models/test_knowledge_models.py -v
python -m pytest tests/unit/models/test_reasoning_models.py -v
python -m pytest tests/unit/models/test_validation_models.py -v
```

### Reasoning

Reasoning tests in this guide verify reusable Project0 reasoning infrastructure, provider abstraction, and deterministic reasoning behavior. Agent-specific prompt behavior and interpretation of reasoning results belong in the applicable Agent Testing Guide.

```bash
python -m pytest tests/unit/reasoning/test_prompt_builder.py -v
python -m pytest tests/unit/reasoning/test_reasoning_service.py -v
python -m pytest tests/unit/reasoning/providers/test_stub_provider.py -v
```

### Validation

```bash
python -m pytest tests/unit/validation/test_markdown_validator.py -v
python -m pytest tests/unit/validation/test_link_validator.py -v
python -m pytest tests/unit/validation/test_mkdocs_validator.py -v
python -m pytest tests/unit/validation/test_documentation_consistency_validator.py -v
python -m pytest tests/unit/validation/test_validation_service.py -v
```

---

### 6.2 Integration Tests

```bash
python -m pytest tests/integration/platform/test_core_platform_flow.py -v
python -m pytest tests/integration/platform/test_context_builder_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
python -m pytest tests/integration/platform/test_knowledge_service_flow.py -v
python -m pytest tests/integration/platform/test_reasoning_service_flow.py -v
python -m pytest tests/integration/platform/test_validation_service_flow.py -v
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
```

Agent-specific integration tests are maintained under the applicable agent integration directory and documented in the applicable `<Agent>_Testing_Guide.md`.

---

### 6.3 Acceptance Tests

Run all acceptance tests:

```bash
python -m pytest tests/acceptance
```

Project0 browser acceptance infrastructure may define the custom pytest option `--ui-slowmo=<milliseconds>`. The option passes the requested delay to Playwright `slow_mo` for human observation. A value of `0` preserves full-speed execution.

Shared interpretation of this option belongs in `tests/acceptance/conftest.py`. Slow-motion execution is an observation aid only; it shall not be used for synchronization or change acceptance criteria.

Agent-specific acceptance commands and browser automation requirements are defined by the applicable `<Agent>_Testing_Guide.md`.

---

### 6.4 Run Complete Test Suites

Run all unit tests:

```bash
python -m pytest tests/unit
```

Run all integration tests:

```bash
python -m pytest tests/integration
```

Run all acceptance tests:

```bash
python -m pytest tests/acceptance
```

Run the complete Project0 test suite:

```bash
python -m pytest
```

---

## 7. Frequently Used Pytest Options

Verbose output:

```bash
python -m pytest -v
```

Stop after the first failure:

```bash
python -m pytest -x
```

Display the slowest tests:

```bash
python -m pytest --durations=10
```

Run a specific test function:

```bash
python -m pytest path/to/test_file.py::test_name -v
```

Run browser acceptance tests visibly:

```bash
python -m pytest tests/acceptance -v -s --headed
```

Run browser acceptance tests visibly with a 750 millisecond observation delay:

```bash
python -m pytest tests/acceptance -v -s --headed --ui-slowmo=750
```

---

## 8. Expected Results

Successful Project0 platform test execution should report all applicable tests passing with no unexpected warnings or failures.

Current Project0 validation expectations include:

- Project0 platform unit tests passing.
- Dashboard Framework unit and integration tests passing.
- Shared platform integration workflows passing.
- Complete Project0 regression suite passing.
- No unexpected warnings or failures.

Agent-specific validation results, behavioral acceptance criteria, and completion requirements are defined by the applicable `<Agent>_Testing_Guide.md`.

The complete Project0 regression suite includes both platform and agent tests. Passing the complete suite therefore remains required before repository-wide changes are considered validated.

As Project0 evolves, the total number of tests will continue to increase. Documentation should be updated periodically to reflect significant platform testing milestones.

---

## 9. Adding New Tests

Each new production component should include corresponding automated tests.

Recommended practice:

1. Implement the production component.
2. Create unit tests.
3. Execute unit tests.
4. Add integration tests where appropriate.
5. Add acceptance tests for externally meaningful user behavior where appropriate.
6. Verify the complete test suite.
7. Commit production code and tests together.

---

## 10. Test Naming Conventions

Recommended file naming:

```
test_<component>.py
```

Recommended function naming:

```
test_<expected_behavior>()
```

Examples:

```
test_repository_service.py

test_repository_reads_markdown()

test_missing_file_returns_error()
```

Test names should describe observable behavior rather than implementation details.

For tests that provide evidence for a verification scenario defined by an agent test plan, the scenario identifier remains independent of the testing layer. The test function name adds a layer prefix.

Integration scenario naming:

```text
test_INT_<scenario_id>_<expected_behavior>()
```

Browser/UI acceptance scenario naming:

```text
test_UI_<scenario_id>_<expected_behavior>()
```

For example:

```text
test_INT_DA_FUN_001_documentation_request_processing()

test_UI_DA_FUN_001_documentation_request_processing()
```

Layer prefixes:

* `INT` — integration verification through assembled Project0 Python/service boundaries.
* `UI` — browser/UI acceptance verification through the actual application boundary.

Scenario identifiers such as `DA-FUN-001` are owned by the applicable agent test plan and should remain stable when the same behavior is verified at multiple testing layers.

---

## 11. Future Enhancements

Future improvements may include:

* Automated code coverage reporting.
* Continuous Integration (CI) execution.
* GitHub Actions integration.
* Performance and benchmark testing.
* Repository health dashboards.
* Static analysis integration.
* Security scanning.
* Scheduled regression testing.

---

## 12. Summary

The Project0 testing framework provides a deterministic, maintainable
foundation for validating platform behavior. Unit, integration, and
acceptance testing verify component behavior, shared Project0 service
interactions, externally observable workflows, Dashboard Framework
behavior, and overall regression stability while agent-specific testing
remains defined by the applicable Agent Testing Guide.
