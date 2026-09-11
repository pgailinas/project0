# Documentation Agent Testing Guide

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

Define the testing strategy, current test organization, execution
commands, browser checks, local-provider checks, repository-safety
requirements, and troubleshooting procedures for the Project0
Documentation Agent.

This guide supplements the repository-wide Project0 Testing Guide. It
does not record a test run or replace the Documentation Agent Test Plan
and Test Results documents.

---

## 2. Objectives

Documentation Agent testing verifies that:

- request, source-path, and target-path input is handled correctly;
- source-grounded and ordinary context paths remain distinct;
- structured reasoning output is parsed and constrained safely;
- source-grounded gap analysis bounds proposal generation;
- invalid, ambiguous, or unsupported proposals fail closed;
- preliminary validation occurs at its actual pre-review boundary;
- each review decision produces the correct repository effect;
- approved changes preserve unrelated content and reject stale targets;
- final validation and Git diff reporting occur after application;
- Dashboard-hosted request and review flows remain usable;
- provider failures and repository failures are reported safely; and
- Documentation Agent changes do not regress shared Project0 services.

---

## 3. Testing Principles

- Use deterministic unit and integration tests for executable
  contracts.
- Use stub providers or controlled fixtures for repeatable reasoning
  output.
- Keep live Ollama evaluation separate from deterministic regression
  claims.
- Use temporary repositories or dedicated test fixtures for all tests
  that can write files.
- Assert both intended mutations and required non-mutations.
- Test public behavior through the narrowest appropriate boundary.
- Add focused regression coverage for every reproducible defect.
- Treat browser acceptance, provider-quality evaluation, and unit tests
  as complementary rather than interchangeable evidence.
- Do not report historical aggregate pass counts as current unless the
  referenced suite was run against the stated commit.

---

## 4. Test Organization

### 4.1 Direct Documentation Agent tests

~~~text
tests/unit/agents/documentation/
    test_documentation_agent_routes.py
    test_documentation_agent_ui_service.py
    test_documentation_agent_view_models.py

tests/acceptance/agents/documentation/
    test_documentation_agent_ui_request_acceptance.py
    test_documentation_agent_ui_review_acceptance.py
    test_documentation_agent_ui_approval_acceptance.py
~~~

### 4.2 Workflow and model tests

~~~text
tests/unit/workflow/test_documentation_workflow.py
tests/unit/workflow/test_review_coordinator.py
tests/unit/models/test_documentation_workflow_models.py
tests/unit/models/test_reasoning_models.py
tests/unit/models/test_validation_models.py
~~~

### 4.3 Supporting service tests

~~~text
tests/unit/reasoning/test_prompt_builder.py
tests/unit/reasoning/test_reasoning_service.py
tests/unit/reasoning/providers/test_ollama_provider.py
tests/unit/reasoning/providers/test_stub_provider.py
tests/unit/repository/test_repository_update_service.py
tests/unit/repository/test_git_diff_service.py
tests/unit/artifacts/test_artifact_location_service.py
tests/unit/artifacts/test_markdown_locator.py
tests/unit/validation/
tests/unit/knowledge/
tests/unit/platform/test_platform_dispatcher.py
tests/unit/dashboard/test_dashboard_app.py
tests/unit/dashboard/test_dashboard_routes.py
tests/unit/skills/test_skill_registry.py
~~~

### 4.4 Integration tests

Documentation behavior is integrated through current platform modules:

~~~text
tests/integration/platform/test_dashboard_flow.py
tests/integration/platform/test_reasoning_service_flow.py
tests/integration/platform/test_ollama_reasoning_flow.py
tests/integration/platform/test_knowledge_service_flow.py
tests/integration/platform/test_validation_service_flow.py
tests/integration/platform/test_platform_dispatcher_flow.py
~~~

The older paths under `tests/integration/agents/documentation/` are not
present in the pinned repository and must not be used in test commands.

---

## 5. Documentation Agent Test Coverage

### 5.1 Request and UI behavior

Verify:

- the ready page and Documentation Agent route render;
- blank requests produce a failed page with a useful message;
- request text is trimmed;
- source and target paths are parsed from newline-separated values;
- empty path lines are discarded;
- workflow exceptions become failed page state;
- page statuses, warnings, errors, summaries, and validation messages
  map correctly;
- focused differences include changed lines and limited context; and
- diff-generation failure is isolated to the proposal view.

### 5.2 Context selection

For requests without source paths, verify Knowledge Service receives the
request and optional targets with baseline inclusion disabled. Empty
targets may trigger ordinary deterministic discovery.

For source-grounded requests, verify:

- only explicitly requested target and source paths are read;
- context labels targets and authoritative sources separately;
- any source-grounded read error fails context construction;
- target headings, not authoritative-source headings, constrain update
  sections; and
- level-one document titles are excluded as update sections.

### 5.3 Two-stage source-grounded reasoning

Verify:

- Stage 1 uses `documentation_gap_analysis`;
- failure in Stage 1 ends the workflow safely;
- no established gaps produces no proposals;
- exact normalized duplicate gaps are removed;
- Stage 2 receives only established gaps;
- Stage 2 uses `documentation_update`;
- the strict documentation skill is loaded for Stage 2 when available;
- Stage 1 does not receive the skill; and
- unsupported Stage 2 output cannot bypass deterministic checks.

### 5.4 Proposal guards

Verify universal rejection of:

- paths outside an explicit target list;
- paths outside the repository;
- missing targets;
- non-Markdown targets; and
- operations other than update.

For source-grounded proposals, also verify:

- meta-instructions are rejected instead of applied as prose;
- inappropriate new fenced Python blocks are rejected or converted to
  valid documentation meaning only when supported;
- uniquely matched Python declarations are canonicalized from source;
- mismatched or ambiguous declarations are rejected;
- missing, duplicate, and ambiguous anchors fail closed;
- semantically unrelated sections are rejected;
- subsection recovery occurs only for one uniquely best positive match;
- a localized section replacement preserves the existing heading; and
- warnings identify each skipped proposal.

### 5.5 Review decisions

Test approve, revise, reject, and skip independently.

- Approve may invoke a repository write immediately.
- Reject and skip produce no write.
- Revise records the decision, retains workflow state, and allows the UI
  to repopulate the request for user resubmission.
- Revise does not automatically generate a replacement proposal.
- Unknown workflows, unknown proposals, and duplicate reviews fail.
- Completion occurs only after every proposal has a decision.

The Review Coordinator has its own unit tests, but the current browser
path submits reviews directly to `DocumentationWorkflow.submit_review()`.

### 5.6 Repository update behavior

Use temporary files to verify:

- proposal and review identifiers must match;
- only approve applies content;
- containment, `.md` type, and file existence are enforced;
- changed content since proposal creation fails the application;
- replace and insert-after modes produce the intended content;
- artifact locations and unique anchors are applied correctly;
- unrelated content is preserved;
- writes use atomic replacement; and
- failures return application records rather than false success.

### 5.7 Validation behavior

The default Documentation Workflow uses Markdown, link, and MkDocs
validators. Documentation Consistency Validator is tested independently
but is not in the default workflow validator tuple.

Verify that:

- preliminary validation receives accepted proposal paths before
  review;
- preliminary validation checks current repository files, not staged
  candidate content;
- preliminary failure is visible with proposals retained for review;
- final validation receives only successfully applied paths;
- no applied paths means no final validation;
- validator exceptions become failed validator results;
- final warnings and failures affect workflow reporting; and
- final validation failure does not roll back an applied file.

### 5.8 Status, state, and completion

Verify workflow statuses, summary counters, warnings, and error fields.
Review state is process-local and should not be tested as durable across
restart. Because warnings can produce a completed-with-warnings public
status while state still exists, UI and workflow tests should also
inspect outstanding proposal decisions.

### 5.9 Dashboard integration

Verify that the agent router is registered, its template uses the shared
Dashboard shell, static assets are mounted, and system status reports
the Documentation-specific model. Confirm that agent-specific business
logic remains in the agent UI service and workflow rather than shared
Dashboard routes.

---

## 6. Running Documentation Agent Tests

All commands assume the repository root and the configured Project0
Python environment.

### 6.1 Documentation Agent UI unit tests

~~~bash
python -m pytest tests/unit/agents/documentation -v
~~~

### 6.2 Documentation Workflow tests

~~~bash
python -m pytest tests/unit/workflow/test_documentation_workflow.py -v
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
python -m pytest tests/unit/models/test_documentation_workflow_models.py -v
~~~

### 6.3 Repository update, diff, and location tests

~~~bash
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
python -m pytest tests/unit/artifacts -v
~~~

### 6.4 Reasoning tests

~~~bash
python -m pytest tests/unit/reasoning/test_prompt_builder.py -v
python -m pytest tests/unit/reasoning/test_reasoning_service.py -v
python -m pytest tests/unit/reasoning/providers -v
~~~

### 6.5 Validation and knowledge tests

~~~bash
python -m pytest tests/unit/validation -v
python -m pytest tests/unit/knowledge -v
~~~

### 6.6 Dispatcher and Dashboard tests

~~~bash
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
python -m pytest tests/unit/dashboard -v
~~~

### 6.7 Relevant integration tests

~~~bash
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
python -m pytest tests/integration/platform/test_reasoning_service_flow.py -v
python -m pytest tests/integration/platform/test_knowledge_service_flow.py -v
python -m pytest tests/integration/platform/test_validation_service_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
~~~

The Ollama integration module has separate live-provider prerequisites:

~~~bash
python -m pytest tests/integration/platform/test_ollama_reasoning_flow.py -v
~~~

### 6.8 Browser acceptance tests

~~~bash
python -m pytest tests/acceptance/agents/documentation -v
~~~

For interactive browser observation, use the options supported by the
repository's acceptance-test configuration, for example:

~~~bash
python -m pytest tests/acceptance/agents/documentation -v -s --headed
python -m pytest tests/acceptance/agents/documentation -v -s --headed --ui-slowmo=750
PWDEBUG=1 python -m pytest tests/acceptance/agents/documentation -v -s --headed
~~~

Playwright automatic waiting must provide synchronization; `slow_mo`
is only for human observation.

### 6.9 Full regression suite

~~~bash
python -m pytest -v
~~~

Run the complete suite before making a current repository-wide pass/skip
claim.

---

## 7. Browser Acceptance and Exploratory Testing

The current Documentation acceptance directory contains request, review,
and approval modules. Use them to verify the actual Dashboard boundary,
not merely the Python workflow API.

Manual or exploratory scenarios should include:

- submit an ordinary request with and without target paths;
- submit a source-grounded request with explicit target and source
  paths;
- confirm source and target filenames remain visible in the form;
- inspect focused differences and proposal rationales;
- reject and skip proposals and confirm no repository change;
- choose revise and confirm the original request can be edited and
  resubmitted;
- approve in a disposable repository and inspect the resulting file;
- inspect preliminary and final validation presentation;
- verify final Git diff and workflow counters;
- verify warnings for rejected proposal content; and
- confirm unrelated files remain unchanged.

Presentation artifacts should be compared with the actual resulting
file before concluding that repository content is damaged.

---

## 8. Local AI Provider Testing

### Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PROJECT0_REASONING_PROVIDER` | Select `ollama` or deterministic `stub` | `ollama` |
| `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | Documentation model override | shared model or `gemma3:4b` |
| `PROJECT0_OLLAMA_MODEL` | Shared model fallback | `qwen2.5:7b` |
| `PROJECT0_OLLAMA_BASE_URL` | Ollama service base URL | `http://127.0.0.1:11434` |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | Provider timeout | 120 seconds |
| `PROJECT0_LOG_LEVEL` | Runtime log level | configured platform default |

### Dashboard startup

~~~bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_DOCUMENTATION_OLLAMA_MODEL=gemma3:4b
python -m project0.main
~~~

Open `/agents/documentation` in the Dashboard. Use
`PROJECT0_REASONING_PROVIDER=stub` for deterministic development flow.

### Live-provider checks

Verify that:

- Ollama is reachable at the configured base URL;
- the selected model is installed;
- provider requests include the expected model and JSON schema;
- the timeout is adequate for the request;
- returned content is a structured JSON object;
- gap analysis identifies only source-established gaps;
- proposals contain concrete Markdown rather than writing instructions;
- warnings and failures are intelligible; and
- no model output bypasses review or deterministic proposal guards.

Live output quality is qualitative evidence and must not be combined
with deterministic automated-test counts.

---

## 9. Repository Safety Acceptance Tests

Before approving a release, verify in a disposable repository that:

- paths outside the root cannot be read or modified;
- non-Markdown and missing targets are rejected;
- proposals outside the explicit target list are skipped;
- missing or ambiguous anchors fail safely;
- unrelated or semantically misaligned sections fail closed;
- source declarations cannot be altered when reproduced in fenced
  Python documentation;
- reject, skip, and revise cause no write;
- approve is the only decision that can write;
- stale original content prevents application;
- one approved file update is atomic;
- unrelated files and content remain unchanged;
- final diff includes only applied paths; and
- failed final validation is reported without being misrepresented as a
  rollback.

Any defect that permits unauthorized or unintended repository mutation
is release-blocking.

---

## 10. Completion Criteria

The Documentation Agent is ready for its current release when:

- focused Documentation Agent unit tests pass;
- relevant platform integration tests pass;
- browser request, review, and approval acceptance tests pass;
- approve, revise, reject, and skip semantics are verified;
- source-grounded two-stage behavior and proposal guards are verified;
- ordinary discovery behavior is verified;
- repository safety and stale-content protection are verified;
- preliminary and final validation behavior is verified at its actual
  boundaries;
- representative live-provider behavior has been reviewed separately;
- the full Project0 regression suite passes; and
- documentation matches the validated implementation.

Record the exact commit, commands, environment, date, and pass/skip
results in the Test Results document. Do not copy historical counts
forward without rerunning the applicable suite.

---

## 11. Regression Testing

When a defect is discovered:

1. Reproduce it in the smallest safe environment.
2. Classify it as route, UI mapping, context, prompt, provider parsing,
   workflow, location, validation, repository update, or diff behavior.
3. Add or update a focused deterministic test when practical.
4. Implement the correction.
5. Run the focused test.
6. Run the owning component suite.
7. Run the relevant integration and browser acceptance tests.
8. Run the full Project0 regression suite.
9. Repeat any affected live-provider scenario separately.
10. Record verified results without overstating unexecuted coverage.

---

## 12. Current Validation Baseline

The repository contains automated unit, platform-integration, and
Documentation Agent browser-acceptance coverage for the areas listed in
this guide. Test presence identifies available coverage; it does not
establish that the tests passed on a particular commit.

No new suite was run as part of the documentation audit that produced
this guide. Therefore, this document intentionally contains no current
aggregate passed/skipped count. The Documentation Agent Test Results
document should record future executions.

---

## 13. Troubleshooting and Future Testing Enhancements

### Troubleshooting

- **Ollama unreachable**: Confirm the service, base URL, selected model,
  and timeout.
- **Structured parsing failure**: Inspect debug output and verify that
  the model follows the supplied JSON schema.
- **No proposals**: Determine whether gap analysis found no material
  gap or all proposals were filtered; inspect warnings and reasoning
  status.
- **Every proposal skipped**: Check target allowlisting, Markdown type,
  location ambiguity, semantic alignment, fenced-code form, and source
  declaration fidelity.
- **Approval failure**: Check repository containment, file existence,
  permissions, and whether the file changed since proposal creation.
- **Workflow ID missing**: Determine whether the process restarted;
  review state is in memory.
- **Final validation failed**: Inspect the written file and validation
  messages directly; no automatic rollback occurs.
- **Acceptance collection failure**: Confirm Playwright and its Chromium
  browser dependency are installed and use repository-supported pytest
  options.

### Future enhancements

Potential additions include candidate-tree validation, restart-recovery
tests, multi-proposal transaction tests if such behavior is implemented,
larger repository fixtures, provider-quality datasets, performance
tests, additional browser scenarios, and CI result publication.

These are testing opportunities, not claims that the corresponding
product capabilities exist.

---

## 14. Summary

Documentation Agent testing combines deterministic component tests,
platform integration tests, browser acceptance tests, repository-safety
checks, and separately reported live-provider evaluation. Together they
verify that documentation proposals are grounded, bounded, reviewable,
and safely applied without confusing available test coverage with an
executed validation result.

---

**End of Document**
