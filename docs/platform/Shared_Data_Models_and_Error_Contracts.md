# Shared Data Models and Error Contracts

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose and Authority

This document describes the shared data models, status values, and error behavior implemented by Project0. It covers platform-level contracts used across repository access, context construction, knowledge selection, reasoning, validation, generic workflows, Documentation workflows, Research workflows, artifacts, and skills.

The Python definitions under `src/project0/models/`, together with the service-specific result and error types identified below, are authoritative. This document does not define a separate serialization schema.

## 2. Design Principles

- Use consistent terms and typed records at component boundaries.
- Keep component contracts independent of internal service implementation where practical.
- Represent expected failure conditions as result status, warnings, issues, or structured service errors when a model exists for that boundary.
- Raise exceptions for invalid construction, malformed calls, unavailable configuration, and failures that the boundary does not convert to a result.
- Keep repository paths repository-relative at public repository and workflow boundaries.
- Preserve deterministic, independently testable model behavior.
- Treat model and enum definitions in source as the contract; do not infer a universal envelope that the implementation does not provide.

## 3. Common Model Conventions

- Shared records are primarily Python dataclasses.
- Most cross-component models use `frozen=True` and `slots=True`.
- Immutability is shallow: a frozen dataclass can still contain mutable objects such as dictionaries.
- Identifiers are strings. Many request, task, proposal, workflow, validation, and document identifiers use UUID4 default factories.
- Timestamps are `datetime` values. Workflow, validation, repository-update, and context-building services generally create timezone-aware UTC timestamps. Current Knowledge and Reasoning results use `datetime.now()` without an explicit timezone.
- Status and operation enumerations use `StrEnum`; their lowercase string values form part of the current contract.
- Collections intended to remain stable are generally tuples. Extensible metadata is generally carried in `dict[str, Any]` fields.
- Convenience properties such as `succeeded`, `has_warnings`, and `has_errors` are local model behavior, not a common result interface.

Project0 does **not** currently implement generic serialized `UserRequest`, `ComponentRequest`, `ComponentResult`, `RepositoryContext`, `ErrorDetail`, or platform-wide `CompletionSummary` models. It also has no common base exception or universal error envelope.

## 4. Model Families and Source Locations

| Family | Authoritative source | Primary role |
| --- | --- | --- |
| Generic workflow | `src/project0/models/workflow_models.py` | Execute a sequence of callable tasks and report task/workflow outcomes |
| Deterministic context | `src/project0/models/context_models.py` | Request and return a bounded documentation context package |
| Repository knowledge | `src/project0/models/knowledge_models.py` | Parse, select, reference, and format repository documents |
| Reasoning/provider | `src/project0/models/reasoning_models.py` | Carry provider-neutral reasoning requests, responses, findings, gaps, and proposed changes |
| Validation | `src/project0/models/validation_models.py` | Request validation and aggregate validator issues/results |
| Artifact location/modification | `src/project0/models/artifact_models.py` | Identify repository locations and controlled modifications |
| Skills | `src/project0/models/skill_models.py` | Carry skill metadata and complete loaded instructions |
| Documentation workflow | `src/project0/models/documentation_workflow_models.py` | Support proposal, human review, application, and completion state |
| Research workflow | `src/project0/models/research_models.py` | Support research strategy, evidence, analysis, evaluation, artifacts, and results |
| Repository operations | `src/project0/repository/repository_service.py` | Return repository metadata, content, batch results, and structured repository errors |

Agent UI view models are presentation contracts owned by their agent packages and are outside this shared platform model inventory.

## 5. Generic Workflow Models

The generic Workflow Engine uses three dataclasses:

| Model | Fields and meaning |
| --- | --- |
| `WorkflowTask` | Task `name`, zero-argument `action`, and generated `task_id` |
| `TaskExecutionResult` | Task identity, `TaskStatus`, start/completion times, optional `output`, and optional `error_message` |
| `WorkflowExecutionResult` | Workflow identity/name, `WorkflowStatus`, start/completion times, ordered task results, and optional `error_message` |

`WorkflowStatus` and `TaskStatus` define `pending`, `running`, `completed`, and `failed`. The current engine returns completed or failed result records; pending and running are defined values but are not persisted or emitted as intermediate results.

The engine executes tasks in order. A task exception is converted to a failed `TaskExecutionResult`, remaining tasks are not executed, and the enclosing `WorkflowExecutionResult` is failed with the same exception text. Successful task outputs remain available in their task results.

The generic engine currently supports the platform's context workflow. It does not orchestrate the stateful Documentation Workflow or the Research Workflow.

## 6. Context and Knowledge Models

### 6.1 Deterministic Context Builder

`ContextWorkflowType` defines:

- `general_documentation`
- `update_documentation`
- `implement_component`
- `validate_documentation`

`ContextBuildStatus` defines `completed`, `completed_with_warnings`, and `failed`.

| Model | Principal fields |
| --- | --- |
| `ContextRequest` | `context_id`, `workflow_type`, and `project_id` (default `Project0`) |
| `ContextDocument` | Repository-relative path, content, byte size, and modification time |
| `ContextPackage` | Identifiers, status, creation time, selected documents, source count, total characters, warnings, and errors |

`ContextPackage.succeeded` is true for completed states, including completion with warnings. Its `has_warnings` and `has_errors` properties reflect the corresponding tuples.

### 6.2 Knowledge Service

The separate Knowledge Service uses:

- `DocumentHeading`: heading level, title, source line, and optional anchor;
- `DocumentLink`: label, target, source line, and internal/external flag;
- `DocumentRecord`: path, title, content, parsed headings/links, tags, modification time, content hash, and metadata;
- `DocumentReference`: selected path/title plus selection reason, score, and matched terms;
- `KnowledgeRequest`: query, workflow type, requested and changed paths, tags, search terms, maximum document count, baseline-document flag, and request identifier;
- `DocumentSelection`: selected records/references plus excluded paths and warnings; and
- `KnowledgeResult`: request identity/query, selection, formatted context, creation time, context metadata, and warnings.

`KnowledgeRequest.maximum_documents` defaults to the configured `KNOWLEDGE_MAXIMUM_DOCUMENTS` value, currently five. Knowledge and deterministic context models are related in purpose but are separate contracts.

## 7. Reasoning and Provider Models

`ReasoningStatus` defines `pending`, `completed`, `completed_with_warnings`, and `failed`.

| Model | Principal fields |
| --- | --- |
| `ReasoningRequest` | Objective, repository context, optional workflow type, target paths, constraints, loaded `SkillDefinition` objects, metadata, and request identifier |
| `ProviderRequest` | System instructions, user prompt, required response schema, optional model/temperature/output-token hints, metadata, and request identifier |
| `ProviderResponse` | Provider/model names, raw content, optional structured output, token/duration/request metadata, warnings, and provider metadata |
| `DocumentationImpact` | Document path, summary, rationale, and optional confidence |
| `DocumentationGap` | Document path, optional section, gap, source evidence, and optional confidence |
| `ProposedDocumentationChange` | Document path, operation, rationale, proposed content, optional meaning/section/anchor, edit type, and confidence |
| `ReasoningResult` | Request identity, status, summary, impacts, gaps, proposed changes, creation time, provider/model identity, assumptions, warnings, optional error, and metadata |

`DocumentationChangeOperation` defines `create`, `update`, and `delete`. `DocumentationEditType` defines `insert`, `replace`, and `delete`. These are provider/reasoning vocabulary; a downstream workflow may deliberately accept a narrower set. In the current Documentation Workflow, source-grounded proposal construction accepts updates to existing target Markdown files and rejects unsupported operations or targets through warnings rather than applying them.

The Reasoning Service converts supported provider, response-parsing, and semantic validation failures into failed `ReasoningResult` values. Provider implementations and callers can still raise exceptions outside those converted paths.

## 8. Validation Models and Aggregation

`ValidationStatus` defines `pending`, `running`, `passed`, `passed_with_warnings`, and `failed`. `ValidationSeverity` defines `info`, `warning`, and `error`.

| Model | Fields and meaning |
| --- | --- |
| `ValidationRequest` | Target repository paths and generated `validation_id` |
| `ValidationIssue` | Validator name, severity, code, message, optional repository path, and optional line number |
| `ValidatorResult` | Validator name, status, start/completion times, issues, and optional error message |
| `ValidationResult` | Validation identity, aggregate status, start/completion times, ordered validator results, flattened issues, and optional combined error message |

The Validation Service runs every configured validator. An unexpected validator exception becomes a failed `ValidatorResult` containing an error-severity issue with code `validator-execution-error`; later validators still run. The aggregate result is failed if any validator fails, otherwise passed with warnings if any validator reports that state, otherwise passed. Validator error messages are combined for the aggregate `error_message`.

## 9. Repository Models and Structured Errors

The repository service defines:

| Model | Purpose |
| --- | --- |
| `RepositoryFile` | Repository-relative path, extension, size, modification time, and documentation flag |
| `FileContent` | `RepositoryFile`, decoded text, and encoding (default UTF-8) |
| `RepositoryQuery` | Optional extension filter and hidden-file inclusion flag |
| `RepositoryListResult` | Discovered files and structured errors |
| `FileReadResult` | One optional file content value and one optional error |
| `FileBatchResult` | Successfully read files and structured errors |
| `RepositoryError` | Error code, user-facing message, optional path, retryable flag, and optional technical details |

`RepositoryErrorCode` values are:

- `invalid_repository_root`
- `file_not_found`
- `path_outside_repository`
- `unsupported_file_type`
- `file_read_error`
- `invalid_request`

List and batch operations can preserve successful items alongside errors. For these models, `succeeded` means that no errors were returned; it does not mean that a non-empty result was produced.

Repository construction errors, including an absent or non-directory root, raise `ValueError`. Malformed caller inputs can also raise exceptions; not every repository failure is represented by `RepositoryError`.

## 10. Artifact and Skill Models

### 10.1 Artifacts

`ArtifactLocationType` defines `file`, `section`, `heading`, and `line_range`. `ArtifactLocation` carries a location identifier, repository path, type, locator, optional start/end lines, and optional content hash.

`ArtifactModificationOperation` defines `insert`, `replace`, and `delete`. `ArtifactModification` combines a location, operation, and content.

The current Markdown locator produces section locations with line ranges. Other location enum values are part of the shared vocabulary but are not all produced by that locator.

### 10.2 Skills

`SkillMetadata` carries a skill's name, description, path, and optional metadata. `SkillDefinition` carries the same identity plus the complete instructions. Skill-registry discovery failures are raised by the registry boundary; there is no skill-specific error-result model.

## 11. Documentation Workflow Models

The stateful Documentation Workflow uses models separate from the generic Workflow Engine.

`DocumentationWorkflowStatus` defines `pending`, `running`, `review_required`, `completed`, `completed_with_warnings`, and `failed`. `ReviewDecision` defines `approve`, `revise`, `reject`, and `skip`. `ChangeApplicationStatus` defines `pending`, `applied`, `skipped`, and `failed`.

`DocumentationAnchorMode` defines legacy `replace` and `insert_after` anchor interpretation. Current proposals can instead carry an `ArtifactLocation` for bounded line-range application.

| Model | Role |
| --- | --- |
| `DocumentationWorkflowRequest` | User request, target/source paths, and workflow identifier |
| `DocumentationChangeProposal` | Existing/proposed content, rationale, optional artifact location or legacy anchor, and proposal identifier |
| `DocumentationReview` | Proposal identifier, decision, optional feedback, and optional review time |
| `AppliedDocumentationChange` | Proposal/path, application status, optional application time, and optional error |
| `DocumentationWorkflowState` | In-memory state retained while review is required |
| `DocumentationWorkflowSummary` | Proposed, decision, application, and failure counts |
| `DocumentationWorkflowResult` | Completed workflow data, preliminary/final validation, Git diff, summary, warnings, and optional error |

Workflow state is held in memory by the Documentation Workflow. It is not durable across process restarts.

Repository Update Service safety or application failures are returned as failed `AppliedDocumentationChange` records. A non-approved review produces `skipped`. Approved changes are limited to existing Markdown files inside the repository. Review/proposal identifier mismatches, path escape, unsupported extensions, absent files, stale content, invalid or ambiguous anchors, and write failures are reported through the application result rather than silently ignored.

Detailed proposal and review semantics belong to the dedicated Documentation Agent documentation.

## 12. Research Models

`research_models.py` defines the Research workflow's shared typed vocabulary, including:

- `ResearchRequest` and `ResearchStrategy`;
- normalized source references and paper metadata;
- ingested context documents;
- evidence references, findings, and existing-research context;
- paper analyses, synthesis, directions, direction analysis, and evaluation;
- research artifacts; and
- the final `ResearchResult`.

The principal status/value enums cover research completion, artifact type, context-document type and extraction status, evidence source type, paper-analysis basis, and paper-evidence availability. Their exact values are authoritative in `research_models.py` and are documented in detail in the dedicated Research Agent documentation.

At the platform boundary, `PlatformDispatcher.run_research_workflow(...)` validates that a workflow is configured and that the question is non-empty, constructs a `ResearchRequest`, optionally passes uploaded context name/content, and returns the configured Research Workflow's `ResearchResult`. The Research Workflow is not executed through the generic Workflow Engine.

## 13. Contract Relationships

The implemented high-level relationships are:

1. `PlatformDispatcher.run_context_workflow(...)` wraps one Context Builder action in a `WorkflowTask` and receives a `WorkflowExecutionResult`.
2. Knowledge selection can build repository context for the Documentation Workflow.
3. The Reasoning Service converts a `ReasoningRequest` into provider-neutral `ProviderRequest`/`ProviderResponse` traffic and returns a `ReasoningResult`.
4. Documentation reasoning proposals are converted to `DocumentationChangeProposal` records suitable for review and controlled application.
5. The Validation Service turns a `ValidationRequest` into per-validator and aggregate validation results.
6. The Documentation Workflow retains a `DocumentationWorkflowState` until reviews are submitted, then applies eligible changes and returns a `DocumentationWorkflowResult`.
7. `PlatformDispatcher.run_research_workflow(...)` passes a `ResearchRequest` directly to the configured Research Workflow and returns a `ResearchResult`.

These are distinct typed paths. Project0 does not route every component interaction through the generic Workflow Engine and does not normalize every outcome into one common result type.

## 14. Error and Failure Contracts

Error behavior is boundary-specific:

| Boundary | Implemented behavior |
| --- | --- |
| Generic Workflow Engine | Converts a task exception to failed task/workflow results and stops subsequent tasks |
| Context Builder | Returns context status, warnings, and errors for supported build outcomes; invalid calls can raise |
| Knowledge Service | Returns selected context plus warnings; malformed input or lower-level failures can raise |
| Reasoning Service | Converts supported provider/parsing/semantic failures to a failed `ReasoningResult` |
| Validation Service | Converts each unexpected validator exception to a failed validator result and continues aggregation |
| Repository Service | Returns `RepositoryError` values for supported discovery/read failures; construction and malformed calls can raise |
| Repository Update Service | Returns failed or skipped `AppliedDocumentationChange` values for controlled-update outcomes |
| Git Diff Service | Raises `RuntimeError` for Git diff failures |
| Platform Dispatcher | Raises `ValueError` for empty required inputs and `RuntimeError` for unavailable optional workflows |
| Startup/configuration/provider factories | Commonly raise `ValueError`, `RuntimeError`, or startup-specific exceptions for invalid or unavailable configuration |

Errors must not be assumed recoverable merely because they are represented as data. Only `RepositoryError` currently carries an explicit `retryable` flag. There is no shared severity taxonomy across all errors: validation uses `info`, `warning`, and `error`, while other model families use statuses, warning strings, error strings, or exceptions appropriate to their boundary.

User-facing layers are responsible for translating these boundary-specific failures into clear messages and available next actions. They must not expose sensitive technical details merely because a lower-level error contains them.

## 15. Persistence, Serialization, and Compatibility

The shared models are ordinary in-process Python objects. The current platform does not provide:

- a generic JSON serialization/deserialization layer;
- a database schema for these contracts;
- durable generic or Documentation workflow history;
- a cross-process event schema; or
- a formal backward-compatibility/versioning mechanism for model fields.

Provider request/response bodies and FastAPI responses use JSON only at their specific boundaries. Callable fields such as `WorkflowTask.action`, `Path` values, `datetime` values, enums, and arbitrary metadata/output objects prevent the Python dataclasses from being treated as a ready-made portable wire format.

Changes to a shared model should update its producers, consumers, interfaces, tests, and documentation together. Compatibility should be preserved where practical, but current source behavior—not this document's version number—is authoritative.

## 16. Future Considerations

The following are possible future extensions, not implemented contracts:

- common request/result envelopes where they provide real value;
- a shared exception hierarchy or error envelope;
- explicit schema validation and JSON serialization;
- consistent timezone-aware timestamps across all model families;
- deep immutable metadata structures;
- durable workflow state and history;
- structured cross-process events and logging correlation; and
- formal model versioning and migration rules.
