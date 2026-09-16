# Testing Guide

**Version:** 0.9  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

This guide defines Project0's implemented test organization, environment, commands, result interpretation, and troubleshooting. Unit, integration, and acceptance tests verify component contracts, production-component collaboration, and externally observable behavior. Test files establish intended coverage only; executed evidence belongs in [Project0 Validation Status](../platform/Project0_Validation_Status.md).

Testing shall be deterministic by default, isolate external systems behind contract-correct fakes, use temporary repositories for file behavior, test observable contracts rather than incidental implementation, and distinguish platform-owned from agent-owned verification. Live providers, browser tests, and recorded results are separate evidence types. Never infer a current pass from inventory, collection, historical counts, or another commit.

## 2. Test Organization and Environment

```text
tests/
├── unit/
├── integration/
│   ├── agents/
│   └── platform/
├── acceptance/
│   ├── agents/
│   └── platform/
└── test_data/
```

Unit tests isolate one service, model, adapter, route, validator, registry, or workflow. Integration tests combine production components across service/application boundaries. Acceptance tests use the intended browser boundary. Live Ollama or provider checks validate one external environment and do not replace regression.

Install from the repository root:

```bash
python -m pip install -e '.[test]'
```

The `test` extra includes pytest and httpx, but not Playwright or its pytest integration. Browser binaries and fixtures must be provisioned separately. The repository currently has no pytest configuration file or checked-in `.github/workflows/` CI definition. Commands assume the intended Python environment is active.

## 3. Test Commands and Procedures

### Standard commands

```bash
python -m pytest
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/acceptance -v
python -m pytest tests/integration/platform -v
```

Agent suites:

```bash
python -m pytest tests/unit/agents/documentation -v
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/unit/agents/research -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
```

Agent-specific workflow modules under `tests/unit/workflow/` belong to their agents. The detailed agent guides define focused files, provider bounds, and acceptance scenarios. `TEST_COMMANDS.md` is the concise command reference.

Useful options are `-v`, `-x`, `--durations=10`, `-s`, a file path, or `path/to/test_file.py::test_name`. Browser `--headed` requires external Playwright pytest support.

### Browser acceptance

Acceptance targets a separately running Dashboard at `http://127.0.0.1:8001` and does not start it.

Terminal 1:

```bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
```

Terminal 2:

```bash
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/acceptance/agents/research -v
```

Visible Research observation:

```bash
python -m pytest \
  tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py \
  -v -s --headed --ui-slowmo=750
```

`--ui-slowmo` defaults to 0 and rejects negatives. It is an observation aid, not synchronization. `tests/acceptance/platform/test_ollama_acceptance.py` is empty and provides no coverage.

### Integrity and change procedure

```bash
python -m compileall -q src
mkdocs build --strict
```

For each material change, identify ownership/behavior; update focused unit tests; add integration or browser coverage where applicable; cover success, warning, failure, validation, and edge paths; run focused then affected suites; run integrity/documentation checks; run the supported complete regression; and commit code, tests, and directly affected documentation together when practical. Empty test files are not evidence.

Use minimal non-sensitive fixtures, temporary roots for writes, contract-correct stubs, and assertions on expected dependency interactions. Test names use `test_<component>.py` and `test_<expected_behavior>()`; multi-layer plan scenarios use `test_INT_<scenario_id>_<behavior>()` or `test_UI_<scenario_id>_<behavior>()`.

## 4. Result Interpretation

A valid record identifies exact source state, date/environment, command/scope, pass/fail/error/skip counts, provider/model mode, browser/external prerequisites, excluded live checks, and separate compilation/documentation results. Do not treat skips as passes, collection as execution, stubs as live validation, or inventory as regression evidence.

`Project0_Validation_Status.md` is manually maintained; the Dashboard displays its bold `Tests` and `Validation` fields but does not execute or verify them.

A repository change is validated only when focused and affected layer suites pass; the complete applicable regression passes; compilation and documentation checks pass where relevant; unexpected warnings/errors/collection failures are resolved; skips and excluded live tests are recorded; and results are tied to the exact source state. Agent criteria may be stricter but cannot replace shared-platform validation.

Current gaps include undeclared browser-test dependencies, no CI workflow, empty Ollama acceptance and `test_skill_models.py` modules, and no automatic repository-health publication. Historical counts must not be carried forward.

## 5. Troubleshooting

- **Acceptance collection fails:** Install Playwright, its pytest integration, and the required browser binaries.
- **Dashboard acceptance cannot connect:** Start the executable Dashboard factory at port 8001 with deterministic providers.
- **Unexpected live dependency:** Confirm tests replace network, model, credentials, and mutable external state at a defined boundary.
- **Integrity check fails:** Treat compilation and strict MkDocs failures independently from pytest results.
- **Historical count differs:** Rerun the applicable command against the current commit and record the new result.
- **Slow or flaky browser test:** Use Playwright waiting/assertions; do not add arbitrary sleeps.

Future CI, coverage thresholds, formatting/type/security gates, live-provider markers, and performance benchmarks remain improvements rather than current validation capability.
