# Shared Data Models and Error Contracts

**Version:** 0.9  
**Owner:** Project0  
**Last Updated:** 2026-09-11  
**Source Baseline:** `main` at `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`

## Purpose and Authority

This reference defines Project0's implemented shared in-process model families,
their authoritative source locations, relationships, and boundary-specific
failure behavior. Source model and enum definitions are authoritative. Agent UI
view models and detailed agent-domain semantics remain in their owning packages
and documentation.

Project0 has no universal request/result envelope, base exception, or error
schema. Callers must honor the contract of the specific boundary.

## Reference Content

### Common conventions and model families

Shared records are primarily frozen, slotted dataclasses; immutability is
shallow. Identifiers are strings, often generated UUID4 values. Collections are
usually tuples and extensible metadata dictionaries. Most service timestamps
are UTC-aware, while current Knowledge and Reasoning results use naive
`datetime.now()`. Status/operation enums use lowercase `StrEnum` values.
Convenience properties are model-specific rather than a shared interface.

| Family | Authoritative source | Role |
| --- | --- | --- |
| Generic workflow | `models/workflow_models.py` | Ordered callable tasks and outcomes |
| Deterministic context | `models/context_models.py` | Bounded documentation context |
| Repository knowledge | `models/knowledge_models.py` | Parse, select, reference, and format documents |
| Reasoning/provider | `models/reasoning_models.py` | Structured reasoning traffic and proposals |
| Validation | `models/validation_models.py` | Validator requests, issues, and aggregation |
| Artifact location | `models/artifact_models.py` | Bounded repository locations/modifications |
| Skills | `models/skill_models.py` | Skill metadata and instructions |
| Documentation workflow | `models/documentation_workflow_models.py` | Proposal, review, application, and state |
| Research workflow | `models/research_models.py` | Strategy, evidence, analysis, evaluation, and results |
| Repository operations | `repository/repository_service.py` | Metadata, content, batches, and structured errors |

All source paths above are beneath `src/project0/`.

### Generic workflow, context, and knowledge

`WorkflowTask`, `TaskExecutionResult`, and `WorkflowExecutionResult` use pending,
running, completed, and failed status values. Tasks run in order; an exception
becomes failed task/workflow results and stops remaining tasks. This engine owns
the generic context path, not the Documentation or Research workflows.

Context contracts include `ContextRequest`, `ContextDocument`, and
`ContextPackage`, with completed, completed-with-warnings, and failed outcomes.
Knowledge contracts separately cover parsed headings/links/documents,
references, requests, selections, and formatted results. Maximum selected
documents defaults to `KNOWLEDGE_MAXIMUM_DOCUMENTS` (currently five).

### Reasoning and validation

`ReasoningRequest` carries objective, context, workflow/targets/constraints,
loaded skills, metadata, and identity. `ProviderRequest`/`ProviderResponse`
define provider-neutral traffic. Findings, impacts, gaps, and proposed changes
flow into `ReasoningResult` with provider/model identity, assumptions, warnings,
errors, and metadata. Reasoning vocabulary includes create/update/delete and
insert/replace/delete, but downstream Documentation Workflow deliberately
accepts a narrower update-only subset.

Validation contracts comprise `ValidationRequest`, `ValidationIssue`,
`ValidatorResult`, and `ValidationResult`, with pending/running/passed/
passed-with-warnings/failed statuses and info/warning/error severities. Every
configured validator runs; unexpected exceptions become failed validator
results and aggregation continues. Any failure fails the aggregate, otherwise
warnings produce passed-with-warnings.

### Repository, artifact, and skill contracts

Repository models represent files, decoded content, queries, list/single/batch
results, and `RepositoryError`. Error codes are `invalid_repository_root`,
`file_not_found`, `path_outside_repository`, `unsupported_file_type`,
`file_read_error`, and `invalid_request`. Batch/list results preserve successful
items beside errors; `succeeded` means no returned errors, not non-empty output.
Construction and malformed-input errors may still raise.

Artifacts use file, section, heading, and line-range locations with optional
content hashes, plus insert/replace/delete modifications. The current Markdown
locator produces section line ranges; not every enum value is produced.

`SkillMetadata` carries name, description, path, and metadata;
`SkillDefinition` adds instructions. Registry discovery/loading errors raise;
there is no skill-specific error-result model.

### Documentation and Research contracts

Documentation Workflow defines pending/running/review-required/completed/
completed-with-warnings/failed workflow states; approve/revise/reject/skip
reviews; and pending/applied/skipped/failed application states. Requests,
proposals, reviews, applied changes, in-memory state, summaries, and final
results are distinct from the generic engine. Approved changes are limited to
existing repository Markdown and enforce identity, containment, extension,
existence, stale-content, location/anchor, and write checks. Non-approved
changes are skipped; failures are reported in application records.

Research contracts cover requests, strategies, normalized sources/papers,
ingested context, evidence, findings, paper analyses, synthesis, directions,
evaluation, artifacts, and `ResearchResult`. Exact status/value enums remain
authoritative in `research_models.py`. Dispatcher validates configuration and a
non-empty question, constructs a request, optionally supplies uploaded context,
and directly returns the Research Workflow result.

### Contract relationships and failures

1. Dispatcher wraps Context Builder in a generic `WorkflowTask`.
2. Knowledge selection supplies Documentation repository context.
3. Reasoning Service converts request/provider traffic into a reasoning result.
4. Reasoning proposals become reviewable Documentation proposals.
5. Validation Service aggregates validator results.
6. Documentation Workflow retains review state, applies eligible changes, and
   returns a dedicated result.
7. Dispatcher passes Research requests directly to Research Workflow.

| Boundary | Failure contract |
| --- | --- |
| Generic engine | Convert task exceptions and stop later tasks |
| Context Builder | Return status/warnings/errors; invalid calls may raise |
| Knowledge Service | Return warnings; malformed/lower-level failures may raise |
| Reasoning Service | Convert supported provider/parsing/semantic failures |
| Validation Service | Convert validator exceptions and continue aggregation |
| Repository Service | Return structured read/discovery errors; some calls raise |
| Repository Update | Return failed/skipped application records |
| Git Diff | Raise `RuntimeError` |
| Dispatcher | Raise `ValueError` for invalid input and `RuntimeError` for unavailable workflows |
| Startup/configuration/factories | Raise boundary-specific exceptions |

Only `RepositoryError` carries an explicit retryable flag. Validation has a
severity taxonomy; other families use statuses, strings, or exceptions. UI
layers translate failures into safe, actionable messages.

## Constraints and Notes

These are ordinary in-process Python objects, not portable wire contracts. The
platform has no generic JSON serialization, database schema, durable workflow
history, cross-process event schema, or formal field-version migration.
Callable tasks, `Path`, `datetime`, enums, and arbitrary metadata/output also
prevent direct treatment as a universal serialized format.

Changes to shared models must update producers, consumers, protocols, tests,
and documentation together. Preserve compatibility where practical, but source
behavior—not this document version—is authoritative.

Possible future work includes useful common envelopes, shared exceptions,
schema validation/serialization, consistently aware timestamps, deeply
immutable metadata, durable state/history, cross-process events and correlation,
and formal model versioning. These are considerations, not implemented
contracts.
