# Documentation Agent Testing Guide

**Version:** 0.9  
**Owner:** Project0  
**Last Updated:** 2026-09-19

## 1. Purpose and Scope

This guide supplements the repository-wide Testing Guide with Documentation Agent verification, commands, browser/live-provider checks, repository-safety requirements, interpretation, and troubleshooting. It does not replace the Test Plan or Test Results.

Testing shall verify both context modes, bounded source-grounded reasoning, fail-closed proposal guards, preliminary/final validation boundaries, all human decisions, stale-content protection, atomic approved writes, path-scoped diffs, Dashboard behavior, explicit failure reporting, and shared-platform regression safety.

## 2. Test Organization and Environment

Direct tests reside under `tests/unit/agents/documentation/` and `tests/acceptance/agents/documentation/`. Workflow/model coverage includes `test_documentation_workflow.py`, `test_review_coordinator.py`, documentation workflow models, reasoning models, and validation models. Supporting tests cover prompt/reasoning/providers, repository update/diff, artifact location/Markdown location, validation, knowledge, dispatcher, Dashboard, and skills.

Relevant integration modules currently reside in `tests/integration/platform/`; older `tests/integration/agents/documentation/` paths are absent and shall not appear in commands.

Live configuration uses `PROJECT0_REASONING_PROVIDER=ollama`, Documentation model override `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` falling back to shared model or `gemma3:4b`, shared default `qwen2.5:7b`, base URL `http://127.0.0.1:11434`, 120-second timeout, and configured log level. Use `stub` for deterministic development. All file-mutating tests shall use temporary/disposable repositories.

## 3. Test Commands and Procedures

```bash
python -m pytest tests/unit/agents/documentation -v
python -m pytest tests/unit/workflow/test_documentation_workflow.py -v
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
python -m pytest tests/unit/models/test_documentation_workflow_models.py -v
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
python -m pytest tests/unit/artifacts -v
python -m pytest tests/unit/reasoning -v
python -m pytest tests/unit/validation -v
python -m pytest tests/unit/knowledge -v
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
python -m pytest tests/unit/dashboard -v
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest -v
```

Relevant platform integration files cover Dashboard, reasoning, knowledge, validation, dispatcher, and separately prerequisite-gated Ollama flow.

For browser observation:

```bash
python -m pytest tests/acceptance/agents/documentation -v -s --headed
python -m pytest tests/acceptance/agents/documentation -v -s --headed --ui-slowmo=750
PWDEBUG=1 python -m pytest tests/acceptance/agents/documentation -v -s --headed
```

Use Playwright waiting for synchronization. Manual scenarios shall verify that request and valid review submissions redirect promptly to `/agents/documentation/runs/{run_id}`, that processing pages update elapsed time and poll run state, and that terminal reload presents review, revision, failure, or completion correctly. Submitted request text, ground-truth source paths, and target documentation paths shall remain populated after approve, revise, reject, and skip decisions and after completed, completed-with-warnings, failed, or review-exception outcomes; New Request shall clear them. Scenarios shall also cover ordinary/source-grounded requests, preserved filenames, rationales/diffs, reject/skip/revise non-mutation, approval in a disposable repository, validation, counters, Git diff, filtered-proposal warnings, and unchanged unrelated files.

Repository-safety acceptance shall confirm root/target containment; Markdown/existence enforcement; fail-closed anchors, semantic locations, and Python declarations; compact Stage 2 context with exactly one proposal-generation call; deterministic assignment of a sole verified claim when model output omits or invents an anchor; deterministic rejection of contradictory fail-closed continuation wording, exact no-ops, replacement or insertion semantic subset restatements, replacements that discard most values from an established inline-code contract enumeration, insertions that expose paired private helpers, and standalone response-detail insertions for identifiers already named by the target; unique normalized-anchor claim selection when multiple established claims share a section; bounded exact-subclaim replacement with preservation of surrounding same-line prose and rejection of unverified narrowing anchors; exact verified-claim anchoring for accepted insertions; continued acceptance of concise corrections and material insertions with new factual values; endpoint-return grounding in returned dictionary fields rather than docstring paraphrases, including retention of a legitimate gap for an absent field; review-required precedence when filtered-proposal or preliminary-validation warnings coexist with retained proposals; ordered application of compatible same-file approvals; continued rejection of an external edit between same-file approvals; fail-closed overlapping, ambiguous, or whole-file combinations; non-writing reject/skip/revise; approval-only writes; stale-snapshot rejection; per-file atomicity; unrelated-content preservation; unique applied-path validation and diff; and explicit failed final validation without implied rollback. Unauthorized mutation is release-blocking.

For a live source-grounded run, DEBUG output should show one Stage 2 `Documentation proposal generation` result, not a corrective proposal retry. Its input token count should reflect the compact rewrite context rather than a saturated full-repository prompt. Review the final anchor and focused difference; token count alone is diagnostic evidence, not acceptance.

## 4. Result Interpretation

The agent is ready only when focused unit tests, relevant platform integration, browser request/review/approval acceptance, all decision semantics, both context modes, safeguards, stale protection, validation boundaries, and full Project0 regression pass; live-provider behavior is separately reviewed; and documentation matches implementation.

Record exact commit, commands, environment, date, and pass/skip results in Test Results. Test presence is coverage inventory, not an execution result. Live qualitative evidence shall not be combined with deterministic counts.

Defect regression proceeds from smallest safe reproduction and classification through focused deterministic test, correction, component suite, integration/browser suites, full regression, separately affected live scenario, and exact result recording.

## 5. Troubleshooting

- **Ollama unreachable:** Confirm service, URL, model, and timeout.
- **Structured parsing failure:** Inspect DEBUG output and schema compliance.
- **No proposals:** Distinguish no material gaps from filtered proposals; inspect warnings/reasoning.
- **Every proposal skipped:** Check allowlist, type, location/anchor ambiguity, semantics, fenced code, and declaration fidelity.
- **Approval failure:** Check containment, existence, permissions, and stale snapshot.
- **Workflow ID missing:** A process restart loses in-memory review state.
- **Run ID missing:** A process restart also loses Dashboard run state and retained page results.
- **Final validation failed:** Inspect the written file and messages; no rollback occurs.
- **Acceptance collection failed:** Install Playwright/Chromium and use supported pytest options.

Future candidate-tree, restart-recovery, transaction, larger-fixture, provider-quality, performance, browser, and CI tests remain opportunities rather than current coverage.
