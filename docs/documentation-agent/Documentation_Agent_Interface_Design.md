# Documentation Agent Interface Design

**Version:** 1.2  
**Owner:** Project0  
**Last Updated:** 2026-09-18

## 1. Purpose and Scope

This document defines the implemented interfaces through which the Documentation Agent receives browser requests, invokes its workflow, presents proposals and validation, accepts individual human decisions, and reports outcomes. The shared Dashboard supplies composition and presentation infrastructure; Documentation-specific routes, models, workflow contracts, reasoning, validation, and repository-update interfaces remain separate.

These interfaces expose a proposal-and-review workflow. They do not authorize unreviewed changes, document creation/deletion, commits, pushes, pull requests, or publication.

## 2. Interface Boundaries

The browser routes accept requests and decisions. The UI Service translates between forms, workflow objects, and page models. The Platform Dispatcher exposes Documentation Workflow operations without the generic Workflow Engine. The process-local workflow coordinates reasoning, validation, review, and application. Provider, validator, location, update, and diff services implement external boundaries.

Browser/UI layers do not select documents, generate edits, validate Markdown, or write files. Presentation differences do not authorize or perform repository mutation. Target scope, repository safety, and application remain deterministic workflow/service responsibilities.

## 3. Interface Contracts

### Browser routes

| Method | Path | Input | Result |
| --- | --- | --- | --- |
| `GET` | `/agents/documentation` | None | Ready Work Area. |
| `POST` | `/agents/documentation/request` | Request and optional source/target paths | Enqueue the workflow and return `303` to its run page. |
| `POST` | `/agents/documentation/review` | Workflow ID, proposal ID, decision, optional feedback | Enqueue a valid decision and return `303` to its run page. |
| `GET` | `/agents/documentation/runs/{run_id}` | Run ID | Render processing, failed, review, revision, or completed state. |
| `GET` | `/agents/documentation/runs/{run_id}/status` | Run ID | Return run lifecycle state and result URL. |

Path fields are newline-separated, trimmed, and stripped of blank entries; route parsing does not guarantee normalization or deduplication. Blank requests fail in UI or dispatcher. Reviews require retained workflow/proposal IDs and one supported decision. Unsupported decision strings render a failed page without creating a run. Valid request and review operations execute through the platform background-run manager rather than inside the originating POST lifetime.

### Platform port

```python
run_documentation_workflow(
    user_request,
    target_paths=(),
    source_paths=(),
    workflow_id=None,
) -> object

submit_documentation_review(workflow_id, review) -> object

get_workflow_state(workflow_id) -> object
```

The dispatcher rejects blank requests/IDs and missing workflow configuration. `get_documentation_workflow_state` remains a backward-compatible alias where implemented.

### Reasoning and validation

The shared reasoning abstraction requires schema-constrained structured gap or update objects; free-form prose is not a proposal. Ollama uses non-streaming `/api/chat`, temperature 0.0, and the supplied JSON schema. Source-grounded prompts include authoritative content and allowed existing target sections, excluding the level-one title. Prompt and skill instructions guide reasoning; deterministic checks govern scope, location, and source fidelity.

The default validation interface runs Markdown, Link, and MkDocs validators; Documentation Consistency Validator is separate. Preliminary validation checks distinct accepted-proposal paths before review; final validation checks successfully applied paths after all decisions. Results expose status, summary, counts, and messages with validator, severity, optional path, and line. Presentation statuses are `not_run`, `passed`, `passed_with_warnings`, and `failed`.

### Update, difference, and presentation

Repository Update Service receives one proposal and matching review. Approval triggers identity, containment, current-content, snapshot, and location checks followed by atomic application. Reject and skip do not write. The UI preview applies the proposal to its original snapshot in memory and renders a focused `ndiff` with three context lines; preview failure is proposal-local.

Page states are `ready`, `processing`, `review_required`, `revision_required`, `completed`, `completed_with_warnings`, and `failed`. The page carries request, workflow ID, proposals, validation, summary, warnings, and error. Revise reloads retained inputs for user editing and resubmission; it does not mutate or regenerate the original proposal.

Configuration uses `PROJECT0_REASONING_PROVIDER`; `PROJECT0_DOCUMENTATION_OLLAMA_MODEL`, falling back through `PROJECT0_OLLAMA_MODEL` to `gemma3:4b`; shared model default `qwen2.5:7b`; `PROJECT0_OLLAMA_BASE_URL` default `http://127.0.0.1:11434`; `PROJECT0_OLLAMA_TIMEOUT_SECONDS` default 120; and `PROJECT0_LOG_LEVEL`. Provider settings are not accepted through the browser.

## 4. Data and Error Contracts

`DocumentationWorkflowRequest` carries request, target/source tuples, and workflow ID. `DocumentationChangeProposal` carries path, complete original snapshot, proposed content, rationale, optional location/anchor, `replace` or `insert_after` mode, and proposal ID. Anchor modes do not authorize create/delete or arbitrary operations.

`DocumentationReview` carries proposal ID, `approve`, `revise`, `reject`, or `skip`, optional feedback, and review time. Approve authorizes immediate application; revise retains state with no write or regeneration; reject/skip write nothing. Decisions are per proposal, not transactional.

`DocumentationAppliedChange` records proposal/path, `pending`, `applied`, `skipped`, or `failed`, optional time, and error. `DocumentationWorkflowState` retains request, reasoning, proposals, reviews, changes, preliminary validation, warnings, and error in process memory. `DocumentationWorkflowResult` adds completion time, final validation, diff, and summary counts.

Workflow statuses are `pending`, `running`, `review_required`, `completed`, `completed_with_warnings`, and `failed`. Consumers must also inspect decisions because warnings may yield completed-with-warnings while proposals remain unreviewed. Summary counters describe workflow records, not Git publication.

Route/UI exceptions produce a failed page; workflow warnings/errors remain separate fields; preview failures remain proposal-local. Unknown workflows/proposals, duplicate reviews, and unsupported decisions are rejected. Application failures remain on the affected record and workflow result. Preliminary-validation failure preserves proposals for inspection.

## 5. Guarantees and Limitations

The interfaces guarantee explicit workflow requests, proposal snapshots, independent human decisions, write authorization only through approval, inspectable review/validation/warning/application outcomes, and non-mutating preview.

They do not provide durable run or workflow state across restarts, shared run state across server processes, automatic run expiration, automatic regeneration after revise, multi-proposal transactions or rollback, document creation/deletion, Git publication, or assurance that every reasoning proposal passes deterministic checks. Final validation does not imply rollback, and prior approved proposals may already be present while later reviews remain pending.
