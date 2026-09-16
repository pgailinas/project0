# Documentation Agent Test Plan

**Version:** 1.1  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

This plan defines verification and acceptance criteria for the Documentation Agent across deterministic unit testing, assembled integration, Dashboard browser acceptance, repository-safety checks, and separate live-provider exploration.

The central safety claim is that model output remains a proposal and only an individually approved, current, valid proposal may modify an existing Markdown file. Verification must prove intended behavior and required non-mutation. Exact commands/environment belong in the Testing Guide; observed outcomes belong in Test Results.

Coverage includes request/context/reasoning, both workflow modes, structured parsing, proposal guards, validation, independent review state, application and stale protection, atomic replacement, Git diff, routes/UI/presentation, Dashboard composition/model status, provider contracts, deterministic stubs, browser acceptance, and shared-platform regression. It excludes generic model benchmarking, guaranteed prose quality, create/delete, transactions/rollback, durable recovery, Git publication, and unrelated agents except shared regressions.

## 2. Verification Strategy

- **Repository grounding:** Accept source-grounded proposals only when traceable to supplied repository evidence and deterministic safeguards.
- **Human authority:** Test `approve`, `revise`, `reject`, and `skip` independently; only approve may authorize a write.
- **Deterministic enforcement:** Verify containment, allowlists, file/operation type, location, source fidelity, validation, stale detection, and application outside model instructions or skills.
- **Safe mutation:** Use temporary/disposable repositories and assert intended content, unrelated-content preservation, and absence of unauthorized writes.
- **Repeatability:** Use stub providers or controlled reasoning for regression; select and report live Ollama checks separately.
- **Evidence-based reporting:** Tie every result to its exact commit and command; the plan does not claim test passage.

Verification levels include direct agent units, workflow/model units, supporting repository/reasoning/location/validation/knowledge/platform/Dashboard/skill tests, current platform integration tests, and three browser modules covering request, review, and approval. Historical `tests/integration/agents/documentation/` paths are not current coverage.

## 3. Test Coverage and Scenarios

### Functional scenarios

- **DA-FUN-001 — Request processing:** Verify ready route, normalized request/path input, blank failure, correct source/target roles, and no invalid-input mutation.
- **DA-FUN-002 — Context selection:** Verify ordinary Knowledge Service behavior with baseline disabled and exact source-grounded reads/labels with fail-closed read errors.
- **DA-FUN-003 — Reasoning mode:** Verify ordinary one-stage updates versus source-grounded gap analysis, deduplication, established-gap-only Stage 2, no-gap behavior, and safe Stage 1 failure.
- **DA-FUN-004 — Proposal construction:** Verify path, snapshot, concrete content, rationale, ID, location/anchor, structured parsing, and deterministic guards before review.
- **DA-FUN-005 — Preliminary validation:** Verify distinct proposal paths, Markdown/Link/MkDocs tuple, pass/warn/fail mapping, retained proposals, and no assumption that Consistency Validator is included.
- **DA-FUN-006 — Review:** Verify one decision per proposal; rejection of unknown/duplicate/unsupported input; immediate approve, non-writing reject/skip, retained revise with repopulated request, and no automatic regeneration.
- **DA-FUN-007 — Application/completion:** Verify immediate per-proposal application, all-decisions completion, applied-path final validation/diff, exact content, non-approved non-mutation, counters, warnings, and errors.
- **DA-FUN-008 — Presentation:** Verify every page state, rationale/difference/decision, validation, counters, and proposal-local preview failure.

### Safety scenarios

- **DA-SAF-001 — Boundaries:** Reject out-of-allowlist/root, missing, non-Markdown, and non-update proposals with no write.
- **DA-SAF-002 — Fail closed:** Reject unsupported claims, ambiguous/missing location, bad anchors/sections/edit types/Python declarations, and level-one title targeting.
- **DA-SAF-003 — Non-approve decisions:** Byte-compare before/after reject, skip, and revise.
- **DA-SAF-004 — Stale proposals:** Change target after proposal generation and verify failed application preserves intervening work.
- **DA-SAF-005 — Minimum change:** Compare original, candidate preview, final file, and Git diff; preserve unrelated content/files.
- **DA-SAF-006 — Non-transactional set:** Approve one proposal while another is pending/rejected and verify independent effects without rollback assumptions.

Any unauthorized or unintended repository mutation is release-blocking.

### Provider, browser, and platform scenarios

Verify provider selection, Documentation-model fallback, Ollama URL/timeout, `/api/chat`, non-streaming JSON schema, temperature 0.0, valid/invalid structured responses, errors/timeouts, and qualitative live grounding without combining it with automated counts.

Browser acceptance shall verify shared-shell rendering, form input, safe failure, deterministic proposals/preliminary validation, proposal path/rationale/difference, non-writing decisions, revision, disposable approval, independent multi-proposal review, final validation/diff/status/counters, unchanged unrelated files, and effective Documentation model status. Playwright waiting—not slow motion—provides synchronization.

Platform regression shall verify route ordering, UI-to-dispatcher calls, direct Documentation Workflow invocation, separation from shared Dashboard business logic, reuse of shared services, and complete Project0 compatibility.

## 4. Environment and Test Data

Deterministic tests shall use temporary roots; concise Markdown/Python fixtures; controlled valid, malformed, unsupported, ambiguous, duplicate, and no-gap reasoning; validator doubles for pass/warn/fail; multiple proposals; and stale-content fixtures.

Principal locations include `tests/unit/agents/documentation/`, `tests/unit/workflow/test_documentation_workflow.py`, documentation/reasoning/validation models, prompt/provider tests, repository update/diff, artifact location, validation, knowledge, dispatcher, Dashboard, skill registry, relevant `tests/integration/platform/`, and `tests/acceptance/agents/documentation/`.

Live Ollama requires `PROJECT0_REASONING_PROVIDER`, `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` falling back through `PROJECT0_OLLAMA_MODEL` to `gemma3:4b`, `PROJECT0_OLLAMA_BASE_URL` default `http://127.0.0.1:11434`, 120-second timeout, and configured logging.

## 5. Entry and Exit Criteria

Entry requires a specific commit, installed selected-level dependencies, disposable roots for writes, and documented live-provider prerequisites.

Exit requires passing focused agent units, relevant platform integration, required browser acceptance or reviewed environmental skips, demonstrated safe writes/non-writes, separately reported live checks, no hidden unresolved failure, complete Project0 regression, and Test Results containing exact commands, commit, outcomes, environment, and known gaps.

## 6. Known Gaps

- Review state is process-local and provides no restart recovery.
- Status verification must inspect outstanding decisions when warnings coexist with retained state.
- The strict skill may guide Stage 2, but deterministic enforcement must be tested independently.
- Live Ollama behavior cannot substitute for deterministic stub coverage.
- This plan intentionally contains no aggregate pass count.
