# Documentation Agent Design

**Version:** 0.7  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

### Objective

Define the detailed component responsibilities, interactions, data
handling, enforcement rules, review behavior, and failure boundaries of
the Project0 Documentation Agent.

### Scope

This document describes how the current components implement the
Documentation Agent Architecture and Functional Specification. It
covers both source-grounded and ordinary documentation requests,
browser review, controlled repository mutation, and validation.

Exact public field declarations and HTTP form contracts belong in the
Documentation Agent Interface Design. Test procedures belong in the
Documentation Agent Test Plan and Testing Guide.

---

## 2. Component Design Principles

- Each component has a focused responsibility.
- Components communicate through typed protocols and immutable models
  where practical.
- Model output is structured but remains untrusted until deterministic
  workflow checks pass.
- Explicit source paths are authoritative, read-only evidence.
- Target Markdown is an existing controlled artifact.
- Repository access, scope enforcement, location resolution,
  validation, file application, and diff generation are deterministic.
- Source-grounded synchronization fails closed when evidence or target
  location is ambiguous.
- Each proposal requires a separate human decision.
- Only approved proposals may modify repository files.
- Agent presentation remains separate from workflow and repository
  behavior.
- The implementation favors minimal localized edits over document
  regeneration.
- Current behavior is distinguished from possible future capability.

---

## 3. Component Overview

The Documentation Agent uses these primary components:

- Dashboard Framework
- Documentation Agent routes
- Documentation Agent UI Service and view models
- Platform Dispatcher
- Repository Service
- Knowledge Service and its parser, index, selector, and formatter
- Prompt Builder
- Reasoning Service and Reasoning Provider
- Skill Registry
- Artifact Location Service
- Documentation Workflow
- Validation Service with Markdown, link, and MkDocs validators
- Repository Update Service
- Git Diff Service
- Shared interfaces and data models

The Platform Dispatcher also exposes a generic Context Builder and
Workflow Engine for platform context workflows. Those services are not
the execution engine for `run_documentation_workflow()`. The current
Documentation Workflow is invoked directly by the dispatcher.

The factory injects a Review Coordinator into the Documentation
Workflow, but interactive browser decisions are submitted directly to
`DocumentationWorkflow.submit_review()` through the Platform
Dispatcher. The stored coordinator is not invoked by that path.

---

## 4. Component Specifications

### 4.1 Dashboard Framework

#### Purpose

Provide the reusable Project0 browser shell in which the Documentation
Agent Work Area is rendered.

#### Responsibilities

- Provide shared layout, navigation, system status, and template
  resources.
- Register the Documentation Agent router before the generic agent
  placeholder route.
- Mount Documentation Agent-specific static resources when present.
- Display the effective Documentation reasoning model in agent context.
- Remain independent of Documentation Workflow business rules.

#### Inputs and outputs

The Dashboard receives FastAPI requests and renders HTML responses. It
passes shared shell context and the Documentation Agent page model to
the Jinja2 template.

### 4.2 Documentation Agent Routes

#### Purpose

Translate HTTP form submissions into UI-service calls.

#### Responsibilities

- Render the ready page at `GET /agents/documentation`.
- Accept `user_request`, `source_paths`, and `target_paths` at
  `POST /agents/documentation/request`.
- Parse source and target paths as trimmed, nonblank, newline-separated
  repository paths.
- Accept workflow ID, proposal ID, decision, and optional feedback at
  `POST /agents/documentation/review`.
- Convert supported decision strings to `ReviewDecision` values.
- Execute synchronous UI-service work in the Starlette thread pool.
- Render unsupported decisions as failed page state.

### 4.3 Documentation Agent UI Service

#### Purpose

Adapt browser requests and domain workflow results without owning
workflow or repository policy.

#### Responsibilities

- Normalize request values.
- Reject blank documentation requests before dispatch.
- Invoke the Documentation Workflow port.
- Construct `DocumentationReview` objects with UTC timestamps.
- Retrieve workflow state after a revise decision so the original
  request, sources, and targets can be repopulated.
- Map workflow objects or mappings to immutable presentation models.
- Convert exceptions into displayable failure pages.
- Derive page status, validation summaries, warning lists, and workflow
  counters.

#### Difference presentation

For each proposal, the service calls the shared
`apply_documentation_change()` helper against the proposal's original
snapshot to construct a candidate full-document result. It compares the
original and candidate with `ndiff`, assigns old and new line numbers,
and shows changed lines with three surrounding context lines.

Difference construction is presentation-only. It does not write a file
and does not replace repository validation. A difference-construction
error is attached to that proposal's view rather than failing the whole
page.

### 4.4 Platform Dispatcher

#### Purpose

Assemble services and expose platform-level Documentation Agent entry
points.

#### Responsibilities

- Validate startup settings.
- Build shared repository, context, workflow-engine, and skill-registry
  services.
- Assemble the Documentation Workflow when a reasoning provider is
  supplied.
- Validate nonblank user requests and workflow identifiers.
- Construct `DocumentationWorkflowRequest` objects.
- Delegate workflow execution, review submission, and state lookup.

#### Design notes

`run_documentation_workflow()` calls `DocumentationWorkflow.execute()`
directly. The dispatcher's generic `WorkflowEngine` is used by the
separate context-workflow API, not by the current Documentation
Workflow path.

### 4.5 Repository Service

#### Purpose

Provide deterministic, read-only repository discovery and file access.

#### Responsibilities

- Normalize and validate repository-relative paths.
- Prevent reads outside the configured repository root.
- Discover supported files and Markdown documentation.
- Read one or multiple repository files.
- Return structured file metadata, content, and errors.

#### Source-grounded use

The Documentation Workflow factory uses Repository Service directly to
read the union of requested target and source paths. Any batch read
error causes source-grounded context construction to fail rather than
silently proceeding with partial authority.

### 4.6 Knowledge Service

#### Purpose

Build deterministic repository-document context for requests that do
not include authoritative source paths.

#### Responsibilities

- Discover Markdown documents.
- Parse document metadata, headings, and links.
- Build an in-memory document index.
- Select documents using the user request and optional requested paths.
- Format selected content into prompt context.
- Preserve warnings in a structured result.

The Documentation Workflow calls Knowledge Service with
`include_baseline_documents=False`. Empty target paths permit ordinary
knowledge discovery; they do not implicitly force baseline documents.

#### Knowledge collaborators

- **Document Parser** converts Markdown into immutable document records.
- **Document Index** provides path-based lookup and deterministic
  ordering while rejecting duplicate paths.
- **Document Selector** handles explicit paths and deterministic
  relevance criteria.
- **Context Formatter** produces ordered provider context without
  changing repository content.

### 4.7 Context Builder, Rule Registry, and Context Filter

These are shared Project0 components used by the dispatcher's generic
context-workflow API. They select repository files from workflow rules
and produce `ContextPackage` objects. They remain relevant platform
dependencies but are not called by the current
`DocumentationWorkflow.execute()` path, which uses either the direct
source-grounded context builder closure or Knowledge Service.

### 4.8 Prompt Builder

#### Purpose

Convert typed reasoning requests into provider instructions, user
prompts, schemas, and metadata.

#### Responsibilities

- Build separate schemas for documentation gap analysis and update
  generation.
- Restrict structured document paths to supplied target paths when
  available.
- Extract eligible headings from target-document context.
- Exclude level-one target titles as source-grounded update sections.
- Enumerate permitted existing sections without inventing headings.
- State source-grounding, minimal-change, concrete-content, anchor, and
  confidence rules.
- Append active skill instructions and record active skill names.

#### Structured stages

`documentation_gap_analysis` requires a summary, gap records,
assumptions, and warnings. Each gap identifies a target document,
optional exact section, gap description, source evidence, and optional
confidence.

`documentation_update` requires a summary, impacts, proposed changes,
assumptions, and warnings. Proposed changes include document path,
operation, rationale, concrete proposed content, optional documentation
meaning, optional exact section and anchor, edit type, and confidence.

### 4.9 Reasoning Service and Provider

#### Purpose

Execute schema-constrained reasoning and convert provider output to
typed results.

#### Responsibilities

- Ask Prompt Builder for a provider request.
- Invoke the configured provider.
- Require structured object output.
- Parse gaps for gap-analysis requests.
- Parse impacts and proposed changes for update requests.
- Normalize supported confidence forms to 0.0–1.0.
- Combine provider and response warnings.
- Convert handled provider, parsing, type, and value exceptions into a
  failed `ReasoningResult`.

The service never reads or writes repository files directly.

The Ollama provider posts a non-streaming request to `/api/chat`, passes
the response schema through `format`, uses temperature 0.0, and parses
the returned message content as a JSON object. Stub mode provides
deterministic structured output.

### 4.10 Skill Registry

#### Purpose

Discover and load validated repository-local Agent Skills.

#### Responsibilities

- Discover skill directories containing `SKILL.md`.
- Validate required metadata and safe skill paths.
- Return metadata separately from complete loaded instructions.
- Preserve immutable skill definitions and deterministic discovery.

When source paths are present and a registry is configured, the
Documentation Workflow loads `strict-documentation-editor` for Stage 2
proposal generation. Stage 1 gap analysis receives no active skill.
Deterministic workflow safeguards remain effective whether or not a
skill is loaded.

### 4.11 Artifact Location Service

#### Purpose

Resolve a proposed documentation edit to a precise existing target
location.

#### Responsibilities

- Discover exact Markdown section locations.
- Support other artifact-location forms used by repository updates.
- Return line ranges and content identity used by proposals.

The workflow first attempts the proposed exact section and then the
proposal rationale. More than one location is ambiguous. For
source-grounded changes, no location is acceptable only when one exact,
unique anchor text is supplied.

### 4.12 Documentation Workflow

#### Purpose

Coordinate the complete proposal, review, application, and completion
life cycle.

#### Request and context behavior

The workflow records start time and obtains context from its injected
context provider. A request with source paths activates source-grounded
behavior. Target paths are converted to path objects for the reasoning
schema and retained as exact allowlist strings for proposal filtering.

#### Source-grounded Stage 1

The first reasoning call uses `documentation_gap_analysis`. Failure
returns a failed workflow result. A successful response with no gaps
creates retained workflow state with no proposals and returns review
state. Otherwise, exact normalized duplicates are removed using document
path, optional section, whitespace-normalized gap text, and
whitespace-normalized source evidence.

The deduplicated gap list is appended to context with an instruction
that Stage 2 must not introduce additional gaps or design changes.

#### Proposal generation

The second source-grounded call, or the sole ordinary call, uses
`documentation_update`. Reasoning failure returns a failed workflow
result. Reasoning warnings are selected according to workflow mode and
the proposed changes are converted individually.

#### Universal proposal checks

Each accepted proposal must:

- use an explicitly allowed target path when a target list exists;
- use the `update` operation;
- resolve inside the repository;
- target an existing regular `.md` file; and
- retain the target's complete original content snapshot.

Unsupported proposals are skipped with warnings.

#### Source-grounded content checks

Source-grounded proposals additionally:

- reject directive or meta-instruction text instead of concrete
  Markdown;
- reject newly introduced fenced Python where the affected target
  section does not already use that form, unless valid prose from
  `documentation_meaning` can safely substitute;
- canonicalize fenced Python declarations when exactly one matching
  authoritative declaration is available;
- reject declarations that do not exactly match authoritative source;
- require a unique resolved location or exact unique anchor;
- reject an explicitly selected section that is semantically unrelated
  to the rationale and content;
- recover to another existing subsection only when one candidate has a
  uniquely highest positive token-overlap score; and
- reject absent, duplicate, ambiguous, or weakly aligned targets.

When a source-grounded replace targets an entire section but the
proposed content does not begin with the exact existing heading, the
workflow narrows the location so the heading is preserved and content is
localized beneath it.

#### Preliminary validation

After proposal construction, the workflow validates the distinct
proposal paths through its configured Validation Service. The request
contains target paths and workflow ID. This checks current repository
files; it does not first stage proposed candidate documents.

A failed preliminary result is returned as failed workflow state with
proposals retained for inspection. A warnings result adds a workflow
warning. Otherwise the workflow returns review-required state.

#### Review processing

Workflow states are held in an in-memory dictionary keyed by workflow
ID. `submit_review()` rejects missing workflows, unknown proposals, and
duplicate reviews.

Revise appends the review and returns retained review-required state. It
does not call the reasoning service. The UI repopulates the request so a
user may modify and resubmit it as a new reasoning cycle.

Approve, reject, and skip are passed with the selected proposal to the
Repository Update Service. Only approve can apply content. If proposals
remain unreviewed, updated state is retained. After all proposals are
reviewed, completion begins.

#### Completion

Successfully applied paths receive final validation. Validation failure
or warnings are recorded, but no rollback is attempted. A Git diff is
generated only when at least one path was applied; otherwise it is an
empty string.

The final result contains request identity, source and target paths,
reasoning, proposals, reviews, application records, both validation
stages, diff, summary counts, warnings, status, and an optional error.
The completed state is then removed from memory.

### 4.13 Validation Service and Validators

#### Purpose

Aggregate deterministic validator results without allowing one
unexpected validator exception to terminate the remaining validation
sequence.

#### Responsibilities

- Invoke configured validators in order.
- Convert an unexpected exception into a failed validator result and an
  error issue.
- Combine all issues and execution errors.
- Return passed, passed-with-warnings, or failed status.

The default Documentation Workflow factory configures Markdown,
internal-link, and MkDocs validators. A Documentation Consistency
Validator exists in the repository but is not included in this default
workflow tuple.

### 4.14 Review Coordinator

#### Purpose

Provide a reusable abstraction for obtaining a decision for a proposal.

The factory injects either a supplied decision provider or an
interactive guard that raises if automatic review is attempted. In the
current interactive Documentation Workflow, the coordinator is stored
but `submit_review()` processes browser-supplied `DocumentationReview`
objects directly. Accordingly, the coordinator is independently tested
but is not the mediator for the Dashboard review path.

### 4.15 Repository Update Service

#### Purpose

Apply a single individually approved Markdown proposal safely.

#### Responsibilities

- Verify that review and proposal IDs match.
- Return skipped status for non-approve decisions.
- Enforce repository containment, `.md` extension, and file existence.
- Read current content and compare it with the proposal snapshot.
- Apply either an artifact-location or unique-anchor change.
- Write UTF-8 content to a temporary file in the target directory.
- Atomically replace the target and clean up temporary content.
- Return applied, skipped, or failed status with an optional error.

The snapshot comparison is optimistic concurrency control. It prevents
application of a proposal based on a stale target document.

### 4.16 Git Diff Service

#### Purpose

Return the Git working-tree difference for successfully applied paths.

It does not stage, commit, branch, merge, push, or publish repository
changes.

### 4.17 Shared Interfaces and Models

Interfaces use structural protocols so implementations can be replaced
in tests or future runtime composition. Relevant contracts cover
repository access, context building, knowledge, reasoning provider and
service behavior, validation, documentation workflow, review,
repository update, artifact location, Git diff, and generic workflows.

Documentation workflow models include:

- workflow statuses: pending, running, review required, completed,
  completed with warnings, and failed;
- decisions: approve, revise, reject, and skip;
- anchor modes: replace and insert after;
- application statuses: pending, applied, skipped, and failed;
- requests, proposals, reviews, applied changes, retained state,
  summaries, and results.

Browser models separately define ready, processing, review-required,
revision-required, completed, completed-with-warnings, and failed page
states plus proposal, difference, validation, and summary views.

---

## 5. Interface Design Principles

- Interfaces remain small and aligned with current capabilities.
- Agent components do not depend on browser form structures.
- Browser presentation does not determine repository authorization.
- Repository paths remain repository-relative at public boundaries and
  are resolved and checked before filesystem use.
- Provider-specific response details remain behind the reasoning
  provider abstraction.
- Structured schemas constrain model output but do not replace runtime
  validation.
- Immutable request and result models preserve reviewability and test
  isolation.
- Backward-compatible aliases may be retained where implemented, but
  documentation identifies the primary current operation.
- Errors and warnings remain explicit fields rather than being encoded
  only in prose summaries.

---

## 6. Component Interactions

### 6.1 Source-grounded request

1. A browser request supplies user text, target paths, and source paths.
2. Routes normalize path lines and call the UI Service.
3. The UI Service calls the Platform Dispatcher.
4. The dispatcher constructs a Documentation Workflow Request.
5. The context provider reads exactly the requested targets and sources.
6. The Reasoning Service performs structured gap analysis.
7. The Documentation Workflow deduplicates established gaps.
8. The Skill Registry loads the strict documentation skill.
9. The Reasoning Service generates proposals bounded to the gaps.
10. The Documentation Workflow applies deterministic proposal guards.
11. The Validation Service validates current accepted target paths.
12. The UI Service renders focused differences and review controls.
13. Each decision is submitted separately.
14. Approved proposals are applied immediately and atomically.
15. After all decisions, applied paths receive final validation and Git
    diff generation.
16. The UI Service renders completion, warnings, or failure.

### 6.2 Ordinary request

The sequence is the same except that Knowledge Service supplies context,
there is no gap-analysis stage, and the strict documentation skill and
source-grounded-only guards are not activated. Universal Markdown,
scope, operation, containment, existence, review, and stale-snapshot
checks still apply.

### 6.3 Revision interaction

A revise decision records the review, performs no write, and returns
revision-required presentation. The UI reloads the original request,
source paths, and target paths from retained state. The user must edit
and resubmit; no automatic provider call occurs as a direct consequence
of the revise decision.

---

## 7. Design Constraints

- The Documentation Workflow is synchronous and process-local.
- Workflow review state is not durable across restarts.
- Only updates to existing Markdown files are executable.
- Source-grounded requests require every requested target and source
  file to be readable.
- Proposal path allowlisting uses exact repository-path strings.
- Source-grounded location and semantic ambiguity fails closed.
- Preliminary validation checks current target files rather than a
  staged candidate repository.
- Decisions are processed one proposal at a time.
- Approval can mutate a file while other proposals remain under review.
- Atomic replacement protects one file write but does not create a
  multi-proposal transaction.
- Final validation does not roll back an applied change.
- The default validation tuple does not include Documentation
  Consistency Validator.
- Intermediate warning status can be exposed while workflow state still
  exists; consumers should inspect outstanding proposal decisions as
  well as the status value.
- The current workflow performs no Git publication operation.
- Live reasoning quality depends on the selected provider and model;
  deterministic schemas and guards constrain but do not eliminate that
  variability.

---

**End of Document**
