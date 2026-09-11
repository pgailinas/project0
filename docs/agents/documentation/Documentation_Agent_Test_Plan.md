# Documentation Agent Test Plan

**Version:** 1.0  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## Executive Summary

This plan defines the verification strategy and acceptance criteria for the
Project0 Documentation Agent. It covers deterministic unit tests, assembled
service integration, Dashboard browser acceptance, repository-safety checks,
and separate exploratory evaluation of live reasoning providers.

The principal safety claim is that AI output remains a proposal until a human
reviews it, and that only an individually approved, current, valid proposal may
modify an existing Markdown file. Tests must establish both intended behavior
and required non-mutation.

This document defines what must be verified. Exact commands and environment
setup belong in the **Documentation Agent Testing Guide**; observed outcomes
belong in **Documentation Agent Test Results**.

## 1. Purpose

The test plan verifies that the Documentation Agent:

- accepts and normalizes documentation requests through its browser interface;
- distinguishes target documentation from authoritative source material;
- produces structured, repository-grounded update proposals;
- rejects unsupported, ambiguous, or out-of-scope proposals;
- validates proposal targets before review;
- preserves an independent human decision for each proposal;
- applies only approved, non-stale changes;
- validates applied paths and reports a final difference;
- presents status, warnings, errors, differences, and counters accurately; and
- remains separated from reusable Project0 platform services.

## 2. Scope

### 2.1 In scope

- Documentation workflow and domain models
- Request, context, reasoning, and proposal processing
- Source-grounded two-stage reasoning
- Ordinary single-stage documentation reasoning
- Structured-output parsing and failure handling
- Proposal allowlisting, containment, location, and semantic guards
- Preliminary and final validation
- Review coordination and retained in-memory state
- Repository application, stale-snapshot protection, and atomic replacement
- Git difference generation
- Documentation Agent routes, UI service, view models, and templates
- Dashboard registration and effective-model display
- Reasoning-provider construction and Ollama request contract
- Deterministic stub-based regression testing
- Browser acceptance and live-provider exploratory checks

### 2.2 Out of scope

- General-purpose model benchmarking
- A guarantee that any local model will produce useful prose for every request
- Creation or deletion of documentation files
- Multi-proposal transactions or rollback
- Durable workflow recovery across process restart
- Git commit, push, pull-request, or publication behavior
- Other agents except where shared platform regression is relevant

## 3. Verification Principles

### 3.1 Repository grounding

Repository content and tests are authoritative. Tests must not accept a proposal
merely because model output asserts that it is correct. Source-grounded updates
must be traceable to supplied authoritative source content and must pass the
workflow's deterministic checks.

### 3.2 Human authority

Every accepted proposal requires an independent `approve`, `revise`, `reject`,
or `skip` decision. Tests must demonstrate that only `approve` can authorize a
write and that review of one proposal does not silently decide another.

### 3.3 Deterministic enforcement

Containment, target allowlisting, file type, operation type, location
resolution, source-fidelity checks, validation, stale-content detection, and
repository application must be tested deterministically. Prompt instructions
and optional skills do not replace these checks.

### 3.4 Safe mutation

Any test capable of writing files must use a temporary repository or dedicated
disposable fixture. It must assert intended content, unrelated-content
preservation, and the absence of unauthorized writes.

### 3.5 Repeatability

Automated regression tests should use stub providers or controlled reasoning
fixtures. Live Ollama tests and qualitative model evaluation must be selected
explicitly and reported separately from deterministic suite results.

### 3.6 Evidence-based reporting

No aggregate pass/skip count is current unless the named suite was executed
against the identified commit. A test plan lists required evidence; it does not
claim that the evidence has passed.

## 4. Test Levels and Current Test Locations

### 4.1 Direct Documentation Agent unit tests

| Area | Principal test path |
|---|---|
| Routes and form parsing | `tests/unit/agents/documentation/test_documentation_agent_routes.py` |
| UI mapping and focused differences | `tests/unit/agents/documentation/test_documentation_agent_ui_service.py` |
| Presentation models | `tests/unit/agents/documentation/test_documentation_agent_view_models.py` |

### 4.2 Workflow and model unit tests

| Area | Principal test path |
|---|---|
| Workflow orchestration and proposal guards | `tests/unit/workflow/test_documentation_workflow.py` |
| Review coordination | `tests/unit/workflow/test_review_coordinator.py` |
| Workflow models | `tests/unit/models/test_documentation_workflow_models.py` |
| Reasoning models and structured parsing | `tests/unit/models/test_reasoning_models.py`, `tests/unit/reasoning/test_reasoning_service.py` |
| Validation models | `tests/unit/models/test_validation_models.py` |

### 4.3 Supporting-service unit tests

| Area | Principal test path |
|---|---|
| Prompt schemas and grounding instructions | `tests/unit/reasoning/test_prompt_builder.py` |
| Ollama and stub providers | `tests/unit/reasoning/providers/test_ollama_provider.py`, `tests/unit/reasoning/providers/test_stub_provider.py` |
| Repository application and stale protection | `tests/unit/repository/test_repository_update_service.py` |
| Git difference generation | `tests/unit/repository/test_git_diff_service.py` |
| Artifact and Markdown location | `tests/unit/artifacts/test_artifact_location_service.py`, `tests/unit/artifacts/test_markdown_locator.py` |
| Validation aggregation and validators | `tests/unit/validation/` |
| Context construction and selection | `tests/unit/knowledge/` |
| Dispatcher composition and delegation | `tests/unit/platform/test_platform_dispatcher.py` |
| Dashboard composition and model display | `tests/unit/dashboard/test_dashboard_app.py`, `tests/unit/dashboard/test_dashboard_routes.py` |
| Strict skill discovery and loading | `tests/unit/skills/test_skill_registry.py` |

### 4.4 Integration tests

Relevant assembled-service coverage is located in:

- `tests/integration/platform/test_dashboard_flow.py`;
- `tests/integration/platform/test_reasoning_service_flow.py`;
- `tests/integration/platform/test_ollama_reasoning_flow.py`;
- `tests/integration/platform/test_knowledge_service_flow.py`;
- `tests/integration/platform/test_validation_service_flow.py`; and
- `tests/integration/platform/test_platform_dispatcher_flow.py`.

Historical paths under `tests/integration/agents/documentation/` are not part of
the current repository and must not be cited as executable coverage.

### 4.5 Browser acceptance tests

The current browser suites are:

- `tests/acceptance/agents/documentation/test_documentation_agent_ui_request_acceptance.py`;
- `tests/acceptance/agents/documentation/test_documentation_agent_ui_review_acceptance.py`; and
- `tests/acceptance/agents/documentation/test_documentation_agent_ui_approval_acceptance.py`.

Browser acceptance verifies the actual Dashboard boundary. It does not replace
workflow, repository, or provider unit tests.

## 5. Functional Verification Scenarios

### DA-FUN-001 — Request processing

Verify that the ready route renders, a valid request reaches the Documentation
Workflow, request text is trimmed, newline-separated source and target paths
are split and trimmed, and blank path lines are removed. A blank request must
produce a failed page with a useful error. Route parsing is not required to
deduplicate paths.

**Pass criteria:** The resulting workflow request preserves the normalized
inputs in the correct source/target roles, and invalid input produces no
repository mutation.

### DA-FUN-002 — Context selection

For an ordinary request, verify that Knowledge Service receives the request and
optional targets with baseline inclusion disabled. Empty targets may use the
implemented deterministic documentation discovery behavior.

For a source-grounded request, verify that only explicitly requested source and
target files are read, the two groups remain distinctly labeled, and any
source-grounded read failure ends context construction safely.

**Pass criteria:** Context reflects the supplied repository files without
conflating authoritative sources and editable documentation.

### DA-FUN-003 — Reasoning mode selection

Verify that requests without source paths use the ordinary single-stage update
path. Verify that requests with source paths first perform
`documentation_gap_analysis`, deduplicate exact normalized gaps, and invoke
`documentation_update` only for established gaps. No-gap output must retain a
valid workflow result with no proposals.

**Pass criteria:** The correct structured schema is used at each stage, Stage 1
failure stops safely, and Stage 2 cannot introduce work beyond established
gaps.

### DA-FUN-004 — Structured proposal construction

Verify that valid reasoning output produces proposals containing repository
path, complete original snapshot, concrete proposed content, rationale,
proposal ID, and any supported location/anchor data. Instructions to write
content are not a substitute for concrete Markdown.

**Pass criteria:** Accepted proposal objects are complete, deterministic guards
run before review, and malformed reasoning output fails or is skipped as the
implementation specifies.

### DA-FUN-005 — Preliminary validation

Verify that the distinct accepted proposal paths are validated before review
using the configured Markdown, link, and MkDocs validators. Confirm that the
Documentation Consistency Validator is not assumed to be in the default tuple.

**Pass criteria:** Passed, warning, and failed results map correctly; validation
failure preserves proposals for inspection but does not present them as
validated changes.

### DA-FUN-006 — Individual review workflow

Verify one decision per proposal and reject unknown workflows, unknown
proposals, unsupported decisions, and duplicate reviews. Approve, reject, and
skip must be forwarded with the selected proposal to the repository-update
boundary. Revise must retain state, repopulate the original request and paths,
and require user resubmission rather than automatically generating a proposal.

**Pass criteria:** Decisions affect only their selected proposal, and outstanding
proposals remain reviewable.

### DA-FUN-007 — Application and completion

Verify that approval is applied immediately for one proposal, even if other
proposals remain undecided. After every proposal receives a decision, verify
final validation of successfully applied paths, final Git difference
generation, completion status, summary counters, warnings, and error fields.

**Pass criteria:** Applied content exactly matches the reviewed proposal,
non-approved proposals do not write, and completion evidence reflects actual
application records.

### DA-FUN-008 — Presentation mapping

Verify ready, processing, review-required, revision-required, completed,
completed-with-warnings, and failed page states. Verify proposal rationale,
focused differences, prior decision state, validation messages, and all summary
counters. Difference-generation failure must remain local to the affected
proposal view.

**Pass criteria:** The browser presents the workflow result without inventing
state or hiding actionable warnings and errors.

## 6. Safety Verification Scenarios

### DA-SAF-001 — Target and repository boundaries

Verify rejection or omission of proposals that target paths outside an
explicit target allowlist, outside the repository root, missing files,
non-Markdown files, or operations other than update.

**Pass criteria:** No unsupported target is written, and each skipped proposal
produces the implemented warning or failure evidence.

### DA-SAF-002 — Source-grounded fail-closed behavior

Verify rejection of unsupported source claims, ambiguous or missing locations,
absent or repeated anchors, invalid section alignment, unrecognized edit types,
and unsupported Python declarations. Verify that the top-level document title
is not treated as an editable target section.

**Pass criteria:** Model output cannot bypass target, grounding, location,
semantic, or declaration checks.

### DA-SAF-003 — Rejected, skipped, and revised proposals

Capture repository content before each decision and verify that `reject`,
`skip`, and `revise` leave it unchanged.

**Pass criteria:** File bytes and unrelated repository state remain unchanged.

### DA-SAF-004 — Stale proposal protection

Modify a target after proposal creation and before approval. Verify that the
Repository Update Service compares current content with the proposal's original
snapshot and refuses the stale application.

**Pass criteria:** Concurrent or intervening edits are preserved and the failed
application is reported.

### DA-SAF-005 — Minimum necessary change

Apply an approved proposal in a temporary repository and compare original and
final content, focused UI difference, and final Git difference.

**Pass criteria:** The intended content changes, unrelated content and files are
preserved, and the reported difference corresponds to the resulting file.

### DA-SAF-006 — Non-transactional proposal set

Use multiple proposals and approve only one while another remains undecided or
is later rejected.

**Pass criteria:** The approved proposal may be present immediately, the other
proposal remains unchanged, and tests do not assume rollback or an all-or-none
transaction.

## 7. Reasoning Provider Verification

### DA-AI-001 — Provider abstraction

Verify dispatcher and provider construction from
`PROJECT0_REASONING_PROVIDER`, including deterministic stub operation and the
current Ollama path.

### DA-AI-002 — Ollama request contract

Verify the effective Documentation model fallback, configured base URL and
timeout, `/api/chat` request, `stream: false`, temperature zero, and JSON-schema
structured-output format.

### DA-AI-003 — Response parsing and failure behavior

Verify valid structured gap/update responses, invalid JSON, schema-invalid
objects, provider errors, and timeout behavior. Unsupported free-form content
must not become an accepted proposal.

### DA-AI-004 — Exploratory grounding quality

With a live local model, manually assess factual grounding, gap relevance,
proposal usefulness, rationale quality, minimality, and hallucination risk.
Record the model and configuration used. Qualitative observations must remain
separate from deterministic pass counts.

## 8. Dashboard and Browser Acceptance

Browser acceptance must cover, at minimum:

1. The Documentation Agent page renders within the shared Dashboard shell.
2. The form accepts request, source-path, and target-path input.
3. Invalid requests are reported safely.
4. A deterministic workflow result presents proposals and preliminary
   validation.
5. Proposal cards display path, rationale, and focused differences.
6. Reject and skip leave the repository unchanged.
7. Revise restores editable request data and does not auto-regenerate.
8. Approval in a disposable repository applies the visible proposal.
9. Multi-proposal review preserves independent decisions.
10. Final validation, Git difference, status, warnings, and counters are shown.
11. Unrelated files remain unchanged.
12. Dashboard system status reports the effective Documentation model.

The acceptance suite should rely on Playwright automatic waiting. Slow-motion
or headed modes are observation aids, not synchronization mechanisms.

## 9. Platform Boundary and Regression Verification

Verify that:

- Documentation routes are registered before any generic placeholder route;
- the UI service calls the Documentation dispatcher port;
- the dispatcher invokes `DocumentationWorkflow` directly;
- agent-specific mapping and business behavior are not embedded in shared
  Dashboard routes;
- shared reasoning, knowledge, validation, repository, artifact, and skill
  services remain reusable; and
- Documentation Agent changes do not regress the complete Project0 suite.

The full repository suite must run before making a repository-wide pass/skip
claim. Results must identify the tested commit, command, environment, and any
intentional skips.

## 10. Test Data and Environment

Deterministic tests should use:

- temporary repository roots;
- small Markdown and Python fixtures with explicit expected content;
- controlled reasoning responses for valid, malformed, unsupported, ambiguous,
  duplicate, and no-gap cases;
- validator doubles for pass, warning, and failure paths;
- multiple proposals for decision-order and counter checks; and
- stale-content fixtures for concurrency protection.

Live Ollama testing additionally requires a reachable configured service and an
installed effective model. The relevant configuration surface is:

| Variable | Purpose | Default or fallback |
|---|---|---|
| `PROJECT0_REASONING_PROVIDER` | Select reasoning provider | `ollama` |
| `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | Documentation model override | Shared model or `gemma3:4b` |
| `PROJECT0_OLLAMA_MODEL` | Shared model fallback | `qwen2.5:7b` |
| `PROJECT0_OLLAMA_BASE_URL` | Ollama service URL | `http://127.0.0.1:11434` |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | Provider timeout | 120 seconds |
| `PROJECT0_LOG_LEVEL` | Runtime logging | Platform default |

## 11. Entry and Exit Criteria

### 11.1 Entry criteria

- The implementation and tests under review identify a specific repository
  commit.
- Dependencies for the selected test levels are installed.
- Writable scenarios use disposable repositories.
- Live-provider prerequisites are documented when those tests are selected.

### 11.2 Exit criteria

- Focused Documentation Agent unit suites pass.
- Relevant platform integration suites pass.
- Required browser acceptance suites pass or documented environment skips are
  reviewed.
- Safety scenarios demonstrate both correct writes and required non-writes.
- Live-provider results, if run, are reported separately.
- No unresolved failure is hidden by an aggregate count.
- Test Results records the exact commands, commit, outcomes, and known gaps.

## 12. Known Coverage Considerations

- In-memory workflow state is not durable and should not be described as
  restart recovery.
- Status tests must inspect outstanding proposal decisions because a general
  warning can yield `completed_with_warnings` while review state still exists.
- Source-grounded Stage 2 may use the strict documentation skill when available;
  tests must still prove deterministic enforcement independently of that skill.
- Live Ollama behavior is environment-dependent and cannot substitute for stub
  regression coverage.
- The plan intentionally records no aggregate pass count. Current counts belong
  only in a Test Results document backed by an executed suite.

---

**End of Document**
