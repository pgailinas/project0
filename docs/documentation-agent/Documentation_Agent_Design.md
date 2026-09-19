# Documentation Agent Design

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Executive Summary

The Documentation Agent uses focused, typed components to turn a source-grounded or ordinary request into reviewable Markdown proposals. Structured model output remains untrusted until deterministic path, operation, content, location, semantic, validation, and stale-snapshot checks pass. Each proposal requires a separate human decision; only approval may write, using per-file atomic replacement. The design favors minimum localized edits, explicit warnings, and separation between browser presentation, workflow policy, and repository mutation.

## 2. Purpose and Scope

This document defines current component responsibilities, interactions, data handling, enforcement, review behavior, configuration, and failure boundaries for the Documentation Agent. It covers source-grounded and ordinary requests, browser review, controlled repository mutation, and validation. Exact public fields and HTTP contracts belong in Interface Design; test procedures belong in the Test Plan and Testing Guide.

The Platform Dispatcher invokes `DocumentationWorkflow.execute()` directly. Its generic Context Builder and Workflow Engine support separate platform context workflows and do not execute the Documentation Workflow. A Review Coordinator is injected, but browser reviews call `submit_review()` directly through the dispatcher.

## 3. Component Design

### Dashboard, routes, and UI

- **Dashboard Framework** owns shared layout, navigation, status, registration order, templates, and static mounting while remaining independent of Documentation business rules.
- **Routes** expose `GET /agents/documentation`, `POST /agents/documentation/request`, and `POST /agents/documentation/review`; parse trimmed newline-separated paths and decisions; run synchronous work in the Starlette thread pool; and render invalid decisions as failed page state.
- **UI Service** normalizes inputs, rejects blank requests, invokes the workflow port, timestamps reviews in UTC, reloads retained state after revise, maps domain models to immutable views, and converts exceptions to displayable failures.
- **Difference presentation** applies the shared change helper to the proposal snapshot in memory, compares original/candidate with `ndiff`, and shows changed lines plus three lines of context. A difference error affects only that proposal and never writes or substitutes for validation.

### Repository and context

- **Repository Service** normalizes contained relative paths, discovers supported files, reads single/batch content, and preserves metadata and read errors. Any source-grounded batch read error aborts complete context construction.
- **Knowledge Service** discovers and parses Markdown, builds an index, selects documents deterministically from the request and optional targets, formats context, and preserves warnings. The workflow sets `include_baseline_documents=False`; empty targets permit discovery rather than implicit baseline inclusion.
- Shared **Context Builder, Rule Registry, and Context Filter** serve the generic context-workflow API and are not called by `DocumentationWorkflow.execute()`.

### Prompting and reasoning

- **Prompt Builder** creates distinct gap-analysis and update schemas, constrains paths and eligible existing sections, excludes level-one titles from source-grounded sections, states grounding/minimum-change/concrete-content/anchor/confidence rules, and appends active skills.
- `documentation_gap_analysis` returns summary, gap records, assumptions, and warnings; `documentation_update` returns summary, impacts, proposed changes, assumptions, and warnings with concrete path, operation, rationale, content, edit type, confidence, and optional meaning/section/anchor.
- **Reasoning Service** invokes the provider, requires structured object output, parses typed gaps or changes, normalizes accepted confidence to 0.0–1.0, combines warnings, and converts handled provider/parsing/type/value failures into failed results. It never accesses the repository.
- **Ollama provider** posts non-streaming `/api/chat` requests with JSON schema and temperature 0.0; stub mode returns deterministic structured output.
- **Skill Registry** validates and loads repository-local skills. `strict-documentation-editor` is active only for source-grounded Stage 2; deterministic safeguards remain authoritative.

### Location, proposals, and workflow

- **Artifact Location Service** discovers exact Markdown sections/ranges. The workflow tries exact section then rationale; multiple matches are ambiguous, and source-grounded missing locations require one exact unique anchor.
- **Documentation Workflow** obtains context, invokes one or two reasoning stages, deduplicates gaps, constructs proposals, applies universal and source-grounded guards, validates current targets, stores review state, processes each decision, applies approved changes, runs final validation, creates a path-scoped diff, reports counters/status, and deletes completed state.

Universal proposal checks require an allowed path when supplied, `update`, repository containment, an existing regular `.md` file, and a complete original snapshot. After location and anchor resolution, the workflow applies the candidate edit in memory and rejects exact no-op results before review. Source-grounded checks reject meta-instructions; unsafe fenced Python; non-authoritative declarations; unresolved, duplicate, ambiguous, or weakly aligned locations; and unsupported section choices. Whole-section replacements preserve the existing heading when necessary.

Stage 1 failure ends the workflow; no gaps retains review state without proposals. Stage 2 receives only deduplicated established gaps and may not introduce new gaps/design changes. Ordinary mode uses one update request. Preliminary validation checks current files, not staged candidates; failure retains proposals for inspection, warnings retain review state.

### Validation, review, and mutation

- **Validation Service** runs configured validators in order, converts unexpected exceptions to failed validator results, and aggregates issues. The default tuple is Markdown, internal-link, and MkDocs validators; it excludes Documentation Consistency Validator.
- **Review Coordinator** is a reusable abstraction and is tested independently, but it does not mediate current browser reviews.
- `submit_review()` rejects unknown workflow/proposal IDs and duplicate decisions. Revise records the decision and restores inputs without reasoning or writing. Approve, reject, and skip go to Repository Update Service; only approve can apply. Completion starts after every proposal has a decision.
- **Repository Update Service** verifies IDs, approval, containment, extension, existence, and the original snapshot; applies an artifact-location or unique-anchor edit; writes UTF-8 through a temporary file and atomic replacement; cleans up temporary content; and returns applied, skipped, or failed. Snapshot comparison provides optimistic concurrency control.
- **Git Diff Service** reports only successfully applied paths and performs no stage, commit, branch, merge, push, or publication action.

### Models and interfaces

Structural protocols cover repository, context, knowledge, reasoning, validation, workflow, review, update, location, diff, and generic workflows. Domain models represent statuses, decisions, anchor modes, application status, requests, gaps, impacts, proposals, reviews, applied changes, retained state, summaries, and results. Browser models separately represent page, proposal, difference, validation, and summary views.

## 4. Interactions and Contracts

Source-grounded processing flows through browser normalization, dispatcher request creation, exact target/source reading, gap analysis, deduplication, strict-skill Stage 2 proposal generation, deterministic guards, preliminary validation, focused-difference presentation, individual decisions, immediate approved application, final validation, applied-path diff, and completion display.

Ordinary processing substitutes Knowledge Service context, omits gap analysis and the strict skill, and retains universal scope, operation, containment, existence, review, and stale-snapshot checks. Revise performs no write or automatic provider call; the user edits and resubmits restored inputs.

Interfaces remain small and typed; browser forms do not determine authorization; relative paths are resolved before filesystem use; provider details remain behind abstraction; schemas constrain but do not replace runtime validation; immutable models preserve reviewability; and errors/warnings remain explicit fields.

## 5. Configuration and Failure Behavior

The Dashboard model resolves from `PROJECT0_DOCUMENTATION_OLLAMA_MODEL`, then `PROJECT0_OLLAMA_MODEL`, with `gemma3:4b` as Documentation fallback. The shared provider may be Ollama or stub; Ollama uses its configured URL and timeout.

Context read failure aborts source-grounded execution. Handled provider, parsing, I/O, runtime, type, and value failures become failed results. Invalid proposals are skipped with warnings. Validator exceptions become error issues without stopping remaining validators. Stale targets fail application. Unknown IDs, duplicate reviews, and unsupported decisions are rejected. Difference-construction errors remain proposal-local.

Final validation records warnings/failure but does not roll back. Intermediate warning status can coexist with retained unreviewed proposals, so consumers must inspect proposal decisions as well as status.

## 6. Constraints and Verification

- Execution and review state are synchronous and process-local.
- Only existing Markdown updates are executable.
- Every requested source-grounded target/source must be readable.
- Allowlisting uses exact repository-path strings.
- Source-grounded ambiguity fails closed.
- Preliminary validation checks current files, not a candidate tree.
- Decisions and writes occur one proposal at a time.
- Atomicity is per file, not across the proposal set.
- Final validation has no rollback.
- Revise does not regenerate automatically.
- Documentation Consistency Validator is outside the default tuple.
- No Git publication operation is performed.
- Live model quality remains variable despite schema and guards.

Verification shall cover both context modes, structured reasoning, gap bounds, proposal enforcement, validation boundaries, all decisions, optimistic concurrency, atomic writes, path-scoped diffs, view mapping, explicit failure reporting, and the separation of shared platform and agent responsibilities.
