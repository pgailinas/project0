# Documentation Agent Interface Design

**Version:** 1.0  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

This document defines the implemented interfaces through which the
Documentation Agent receives browser requests, invokes its workflow, presents
proposals and validation results, accepts human decisions, and reports final
outcomes.

The Documentation Agent is hosted by the Project0 Dashboard Framework. The
Dashboard supplies the shared application shell, navigation, templates, and
runtime composition. Documentation-specific routes, view models, and workflow
contracts remain separate from the shared presentation framework and from the
agent's reasoning and repository-update internals.

These interfaces expose a proposal-and-review workflow. They do not authorize
automatic publication, commits, pushes, pull requests, or unreviewed file
changes.

## 2. Interface Boundaries

The implemented interface is divided into five boundaries:

1. Browser routes accept documentation requests and individual proposal
   decisions.
2. The Documentation UI Service translates between form data, workflow domain
   objects, and page view models.
3. The Platform Dispatcher exposes Documentation Workflow operations to the UI
   without routing them through the generic Workflow Engine.
4. The Documentation Workflow retains in-memory state and coordinates
   reasoning, validation, review, and application.
5. Provider, validation, and repository services implement the external
   reasoning, checking, and file-update operations.

The browser and UI layers do not select documents, generate edits, validate
Markdown, or write repository files directly.

## 3. Browser Routes

The Documentation Agent router uses the prefix `/agents/documentation`.

| Method | Path | Input | Result |
|---|---|---|---|
| `GET` | `/agents/documentation` | None | Renders the Documentation Work Area in the ready state. |
| `POST` | `/agents/documentation/request` | `user_request`, optional `source_paths`, optional `target_paths` | Starts the synchronous documentation workflow and renders its current result. |
| `POST` | `/agents/documentation/review` | `workflow_id`, `proposal_id`, `decision`, optional `feedback` | Submits one proposal decision and renders the updated workflow state. |

### 3.1 Request form contract

`user_request`, `source_paths`, and `target_paths` are submitted as form
fields. Both path fields are newline-separated text. Route parsing splits them
on line boundaries, trims surrounding whitespace, and removes blank entries.
It does not promise path normalization or duplicate removal.

The request endpoint passes target paths before source paths to the platform
port, matching the port's keyword-oriented signature. A blank request is
rejected by the UI service or dispatcher and is shown as a failed page.

### 3.2 Review form contract

The review endpoint requires all of the following:

- a retained workflow ID;
- a proposal ID belonging to that workflow; and
- one supported decision string.

The optional feedback field is preserved in the review object. Unsupported
decision strings render a failed page instead of being forwarded to the
workflow.

Dashboard route handlers execute the synchronous UI-service calls in a worker
thread so they do not directly block the asynchronous route handler.

## 4. Platform Port

The Documentation UI Service depends on the following operations:

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

The dispatcher validates blank user requests and blank workflow identifiers.
It also reports missing Documentation Workflow configuration. The
Documentation Workflow is invoked directly; the generic agent Workflow Engine
is not part of this execution path.

`get_documentation_workflow_state` remains a backward-compatible dispatcher
alias for `get_workflow_state` where exposed by the platform implementation.

## 5. Workflow Domain Models

### 5.1 Request

`DocumentationWorkflowRequest` carries:

- `user_request`;
- `target_paths`, as a tuple;
- `source_paths`, as a tuple; and
- `workflow_id`, generated when one is not supplied.

Target paths constrain the documentation files that proposals may update.
Source paths identify authoritative implementation material for grounded
analysis. The exact selection, discovery, and grounding rules are workflow
behavior, not browser-interface guarantees.

### 5.2 Change proposal

`DocumentationChangeProposal` carries:

- `repository_path`;
- the complete `original_content` snapshot;
- `proposed_content`;
- `rationale`;
- optional `artifact_location`;
- optional `anchor_text`;
- `anchor_mode`, defaulting to `replace`; and
- a generated `proposal_id`.

Supported anchor-mode values are `replace` and `insert_after`. They are legacy
application interpretations within the current full-content proposal model;
their presence does not expand the workflow to file creation, deletion, or
arbitrary repository operations.

### 5.3 Review

`DocumentationReview` carries:

- `proposal_id`;
- `decision`;
- optional `feedback`; and
- optional `reviewed_at` time.

Supported decision values are:

| Decision | Interface effect |
|---|---|
| `approve` | Authorizes the Repository Update Service to attempt this proposal immediately. |
| `revise` | Retains workflow state and returns an editable revision-required presentation. It does not generate a replacement proposal automatically. |
| `reject` | Records the decision and does not write the proposal. |
| `skip` | Records the decision and does not write the proposal. |

Every accepted proposal requires its own decision. Approval is per proposal,
not a transaction across the proposal set. Consequently, earlier approved
changes may already exist in the working tree while other proposals await
review.

### 5.4 Applied change

`DocumentationAppliedChange` records:

- `proposal_id`;
- `repository_path`;
- application `status`;
- optional `applied_at` time; and
- optional `error_message`.

Application status values are `pending`, `applied`, `skipped`, and `failed`.
Only an approved proposal can result in `applied`.

### 5.5 Retained workflow state

`DocumentationWorkflowState` retains, in memory:

- workflow ID and workflow status;
- start time and original request fields;
- reasoning result;
- proposals, reviews, and applied changes;
- preliminary validation;
- warnings; and
- an optional error message.

State is process-local and is not a durable workflow store. Restarting the
process can make a previously issued workflow ID unavailable.

### 5.6 Workflow result

`DocumentationWorkflowResult` adds completion time, final validation, optional
Git diff, summary counters, warnings, and an optional error to the retained
workflow data.

Workflow status values are:

- `pending`;
- `running`;
- `review_required`;
- `completed`;
- `completed_with_warnings`; and
- `failed`.

Consumers must also inspect proposal decisions. In an intermediate edge case,
general workflow warnings can produce `completed_with_warnings` while
unreviewed proposals still exist; status alone is therefore not a sufficient
review-completion signal.

## 6. Reasoning Provider Interface

The Documentation Workflow uses the shared reasoning-provider abstraction.
The current Ollama provider sends a non-streaming request to `/api/chat`, sets
temperature to zero, and supplies the required JSON schema through the
provider's structured-output format field.

Reasoning results must satisfy the configured structured gap-analysis or
proposal schema. The Reasoning Service parses structured gap and update
objects; free-form prose is not treated as an update proposal.

For source-grounded requests, the prompt builder supplies authoritative source
content and derives the allowed target section headings. The target document's
top-level title is excluded from the editable section-heading set. Prompt and
skill guidance assist reasoning, but deterministic workflow checks remain the
authority for proposal scope, location, and source fidelity.

## 7. Validation Interface

The default Documentation Workflow validation pipeline consists of:

- Markdown validation;
- link validation; and
- MkDocs validation.

The Documentation Consistency Validator exists separately but is not included
in the default validator tuple.

Preliminary validation runs against the distinct paths of accepted proposals
before review. Final validation runs after all proposals have decisions and is
limited to successfully applied paths. Validation results expose a status,
summary, error and warning counts, and individual messages.

Presentation-level validation statuses are:

- `not_run`;
- `passed`;
- `passed_with_warnings`; and
- `failed`.

Each displayed validation message includes validator name, message, severity,
and optional repository path and line number.

## 8. Repository Update and Difference Interfaces

The Repository Update Service receives one proposal and one matching review.
For an approval it verifies proposal/review identity, re-reads the current
target, compares it with the proposal's original snapshot, and refuses stale
content. A supported artifact-location or unique-anchor operation is then
applied atomically. Reject and skip produce no write.

The UI's proposal difference is a display artifact, not an application
instruction. It applies the proposal to the original snapshot in memory and
uses a focused `ndiff` view with three context lines. Difference-line types are
`context`, `added`, `removed`, and `header`; old and new line numbers are
optional.

If difference construction fails, the error is attached to that proposal's
difference view. The remaining page can still render. Neither previewing a
difference nor rendering a proposal changes the repository.

## 9. Presentation Models

### 9.1 Page states

`DocumentationAgentPageStatus` supports:

- `ready`;
- `processing`;
- `review_required`;
- `revision_required`;
- `completed`;
- `completed_with_warnings`; and
- `failed`.

The page view carries its status and message, the request form, optional
workflow ID, proposal views, preliminary and final validation, optional
workflow summary, warnings, and an optional error message. Convenience
properties expose whether review is required and whether warnings or an error
are present.

### 9.2 Request and revision presentation

`DocumentationRequestForm` contains the user request and source/target path
tuples. When a reviewer selects `revise`, the UI service reloads the retained
workflow state and repopulates these fields. The user can then edit or append
instructions and submit a new workflow request through the ordinary request
route. Revision does not mutate the original proposal and does not imply
automatic regeneration.

### 9.3 Proposal presentation

Each `DocumentationProposalView` contains the proposal ID, repository path,
rationale, original and proposed content, optional selected decision and
feedback, and an optional focused difference. Proposal cards display the path,
rationale, difference, controls, and prior decision state.

### 9.4 Summary presentation

`DocumentationWorkflowSummaryView` reports counts for:

- proposed;
- approved;
- revised;
- rejected;
- skipped;
- applied; and
- failed items.

These counters describe workflow records; they do not imply a Git commit or
publication result.

## 10. Configuration Interface

| Setting | Environment variable | Effective default or fallback |
|---|---|---|
| Reasoning provider | `PROJECT0_REASONING_PROVIDER` | `ollama` |
| Documentation Ollama model | `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | `PROJECT0_OLLAMA_MODEL`, otherwise `gemma3:4b` |
| Shared Ollama model | `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` |
| Ollama base URL | `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| Ollama timeout | `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | 120 seconds |
| Log level | `PROJECT0_LOG_LEVEL` | Platform logging default |

The Dashboard system-status interface reports the effective Documentation
model when queried for the Documentation Agent. Configuration determines
provider construction; the browser form does not accept provider credentials,
model names, or base URLs.

## 11. Error Interface

The interface distinguishes three error scopes:

- Route or UI-service exceptions render a failed Documentation Agent page.
- Workflow warnings and workflow errors remain separate fields in retained
  state and results.
- Difference-construction failures remain local to the affected proposal view.

The workflow rejects an unknown workflow ID, an unknown proposal ID, and a
duplicate review. The route rejects an unsupported decision string. Repository
application failures are recorded on the affected applied-change record and in
the resulting workflow outcome as appropriate.

Preliminary validation failure preserves proposals for inspection but prevents
them from being treated as successfully validated changes. Validation warnings
are presented separately from errors.

## 12. Interface Guarantees and Limitations

The current interfaces guarantee that:

- browser input is translated into explicit workflow request objects;
- structured proposals retain their original-content snapshots;
- each proposal has an independent human decision;
- only approval can authorize a file write;
- review, validation, warning, and application outcomes remain inspectable; and
- proposal preview does not itself mutate repository content.

The current interfaces do not provide:

- durable workflow persistence across process restarts;
- automatic proposal regeneration after `revise`;
- a multi-proposal transaction or rollback;
- creation or deletion of documentation files through the proposal workflow;
- commit, push, pull-request, or publication operations; or
- a browser guarantee that every reasoning proposal will pass deterministic
  workflow checks.

---

**End of Document**
