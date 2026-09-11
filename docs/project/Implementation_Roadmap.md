# Implementation Roadmap

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose and Status Authority

This roadmap records Project0's phased implementation history, the capability delivered by each phase, the dependency sequence, current corrective priorities, and possible future expansion.

The roadmap is not a test-results record. Repository-visible implementation and verification status belong in [Implementation Status](Implementation_Status.md) and [Project0 Test Results](../platform/Project0_Test_Results.md). A phase's presence in source does not by itself establish that every test or acceptance criterion passes at the current commit.

The phases are historical planning boundaries. Ongoing work can improve an earlier phase without creating a new phase number.

## 2. Delivery Strategy

Project0 evolves through small, testable, end-to-end capabilities. Development emphasizes:

- modular components with typed interfaces and models;
- deterministic processing wherever model reasoning is unnecessary;
- dependency injection and deterministic substitutes for testing;
- human review before Documentation Workflow repository writes;
- agent-specific behavior separated from reusable platform services;
- source-grounded documentation and explicit limitations; and
- validation throughout implementation rather than only at a final milestone.

Priority is given to complete, reviewable vertical capabilities over disconnected architectural scaffolding. Architecture should evolve from demonstrated requirements while preserving clear ownership and stable contracts.

## 3. Phase Summary

| Phase | Name | Repository-visible state at pinned commit |
| --- | --- | --- |
| 1 | Foundation | Implemented |
| 2 | Core Platform Services | Implemented |
| 3 | Repository Knowledge Services | Implemented with in-memory, non-semantic retrieval boundaries |
| 4 | AI Reasoning Integration | Implemented for Ollama and deterministic stub reasoning |
| 5 | Validation Services | Implemented; default Documentation Workflow composition omits Documentation Consistency |
| 6 | Workflow Integration | Implemented for Documentation review/update flow and Git diff generation |
| 7 | Dashboard Framework | Implemented with documented shared limitations |
| 8 | Documentation Agent User Interface | Implemented |
| 9 | Testing and Verification | Test layers and sources implemented; current pinned-commit result not established |
| 10 | Platform Validation Consolidation | Partially realized; no separate Platform Test Plan exists |
| 11 | Research Agent Foundation and Functional Validation | Implemented in source and agent test suites |
| 12 | Documentation Agent Enhancement | Implemented in source and tests |
| 13 | Research Agent Context-Aware Literature Analysis | Implemented in source and tests |
| 14 | Project0 Agent Skills Foundation | Implemented; current repository-wide verification incomplete |

The status summary is deliberately more precise than the earlier blanket use of “completed.” Current source contains work corresponding to every phase, but the pinned audit could not establish an unconditional all-phases-passing result and identified repository-level gaps.

## Phase 1 — Foundation

### Objective

Establish the repository and runtime foundation required for Project0 development.

### Delivered capability

- Python 3.12+ package metadata and `src` layout;
- Markdown documentation organized for Material for MkDocs;
- shared environment-based configuration;
- application logging setup;
- startup directory/file validation; and
- project-level development, documentation, and testing guidance.

### Repository evidence

`pyproject.toml`, `mkdocs.yml`, `src/project0/config/`, `src/project0/common/`, `README.md`, and `docs/project/`.

### Current boundaries

No dependency lock, checked-in continuous-integration workflow, containerized environment, or formal cross-platform support matrix is present.

## Phase 2 — Core Platform Services

### Objective

Implement reusable platform services required by agent workflows.

### Delivered capability

- read-only Repository Service with containment and supported-file checks;
- generic sequential Workflow Engine;
- deterministic Context Builder;
- shared protocols and typed models; and
- Platform Dispatcher composition.

### Current boundaries

The generic Workflow Engine owns generic task sequences and the context workflow. The stateful Documentation Workflow and Research Workflow are dispatched directly through their dedicated coordinators; they are not orchestrated by the generic engine.

## Phase 3 — Repository Knowledge Services

### Objective

Provide deterministic repository-document parsing, selection, and context formatting for reasoning workflows.

### Delivered capability

- Markdown parsing for headings, links, tags, metadata, and content;
- per-request in-memory document indexing;
- deterministic filtering and ranking;
- bounded document selection;
- formatted reasoning context; and
- coordinated Knowledge Request/Result processing.

### Current boundaries

The current Knowledge Service scans repository Markdown under `docs/` for each request. It has no embeddings, vector database, semantic search backend, or durable index.

## Phase 4 — AI Reasoning Integration

### Objective

Add provider-neutral, structured AI reasoning without moving deterministic policy into the model.

### Delivered capability

- provider-neutral request and response models;
- prompt construction with required response schemas;
- Reasoning Service parsing and validation;
- Ollama provider support;
- deterministic stub provider behavior; and
- structured documentation impacts, gaps, and change proposals.

### Current boundaries

The executable Dashboard reasoning-provider factory accepts `ollama` and `stub`. Additional provider names are not implemented at that boundary. Model output remains subject to deterministic downstream validation and workflow rules.

## Phase 5 — Validation Services

### Objective

Provide structured, composable validation for repository documentation.

### Delivered capability

- Markdown validation;
- local-link and referenced-file validation;
- strict MkDocs build validation;
- documentation-consistency validation;
- ordered validation aggregation; and
- per-validator exception isolation with structured issues.

### Current boundaries

The default Documentation Workflow assembles Markdown, Link, and MkDocs validators. `DocumentationConsistencyValidator` is implemented and used explicitly in integration coverage but is not part of that default tuple. Source, tests, and documentation should be aligned before claiming it as a default workflow gate.

## Phase 6 — Workflow Integration

### Objective

Integrate documentation reasoning, review, controlled updates, validation, and Git diff reporting into a stateful workflow.

### Delivered capability

- Documentation Workflow request and in-memory review state;
- source-grounded gap analysis and proposal generation;
- per-proposal review decisions;
- constrained Markdown update application;
- stale-content, path, extension, location, and anchor safeguards;
- preliminary and final validation; and
- Git diff generation and completion summaries.

### Current boundaries

Workflow state is in process memory rather than durable storage. The platform does not automatically commit, push, open a pull request, publish, or deploy changes.

Detailed behavior belongs in `docs/agents/documentation/`.

## Phase 7 — Dashboard Framework

### Objective

Provide a shared browser shell for Project0 services and registered agent interfaces.

### Delivered capability

- FastAPI application and executable factory;
- Jinja2 shared layout;
- navigation and shared status presentation;
- home, agent-launch, health, and documentation routes;
- static CSS mounting;
- agent route registration; and
- fallback handling for unavailable agent routes.

### Current boundaries

`/activity` and `/settings` are navigation-only links without implemented pages. The shared Dashboard has no authentication, durable workflow history, server-side telemetry store, dynamic plugin registration, or automatic documentation-server startup. The displayed project-phase label is hard-coded and currently stale.

## Phase 8 — Documentation Agent User Interface

### Objective

Expose the Documentation Workflow through a Dashboard-hosted, human-review interface.

### Delivered capability

- request entry;
- proposal and difference presentation;
- validation presentation;
- per-proposal approve, revise, reject, and skip decisions; and
- completion-result presentation through an agent-owned router, UI service, view models, templates, and CSS.

Detailed behavior and validation remain in `docs/agents/documentation/`.

## Phase 9 — Testing and Verification

### Objective

Establish deterministic unit, integration, and acceptance validation across platform and agent behavior.

### Delivered capability

- unit-test organization for models and components;
- integration tests for assembled platform and agent workflows;
- browser acceptance sources for Dashboard-hosted agent interfaces;
- deterministic stub paths; and
- reusable commands in `TEST_COMMANDS.md` and testing guides.

### Current boundaries

Test-source presence is not a pass result. Browser tests depend on Playwright packages and browser fixtures not declared in `pyproject.toml`. The pinned audit environment lacked pytest and could not establish a current regression count. One source file also fails Python compilation, as recorded below.

## Phase 10 — Platform Validation Consolidation

### Objective

Separate reusable platform verification ownership from agent-specific verification and consolidate platform test guidance and results.

### Delivered capability

- platform-level Testing Guide;
- shared Project0 Test Results record;
- platform versus agent testing boundaries;
- platform integration coverage; and
- documentation-consistency rules for required documents and roadmap/status phase references.

### Current boundaries

The earlier roadmap listed a platform test-coverage matrix and separate Project0 Platform Test Plan as deliverables. No separate Platform Test Plan file exists in the repository. The current Testing Guide and test sources supply much of that operational coverage, but the absent deliverable must not be reported as complete.

## Phase 11 — Research Agent Foundation and Functional Validation

### Objective

Add a second specialized agent and demonstrate reusable platform composition beyond the Documentation Agent.

### Delivered capability

- Research models and protocols;
- strategy, query, source, metadata, evaluation, artifact, and workflow services;
- Semantic Scholar, OpenAlex, OpenReview, Crossref, arXiv, and stub source adapters;
- Dashboard registration and agent-owned interface layers; and
- agent-specific unit, integration, and browser acceptance sources.

Detailed requirements, architecture, behavior, and test evidence remain in `docs/agents/research/`.

## Phase 12 — Documentation Agent Enhancement

### Objective

Improve source-grounded documentation maintenance and controlled, localized updates.

### Delivered capability

- explicit source and target context;
- two-stage gap and proposal reasoning for source-grounded work;
- artifact-location discovery and validation;
- localized proposal handling;
- source-evidence and target-scope guards;
- stale-content protection; and
- deterministic enforcement outside model instructions.

Detailed behavior remains in the dedicated Documentation Agent documentation.

## Phase 13 — Research Agent Context-Aware Literature Analysis

### Objective

Extend literature retrieval into evidence-aware analysis that can incorporate optional existing research context.

### Delivered capability

- PDF, Markdown, and text context ingestion;
- existing-context analysis with provenance;
- context-aware strategy and multi-query retrieval;
- bounded source and evaluation processing;
- research-paper evidence acquisition;
- per-paper analysis;
- consolidated retained-paper evaluation;
- cross-paper synthesis;
- evidence-grounded Research Direction Analysis; and
- workflow and Dashboard integration while preserving no-context execution.

Detailed behavior and limitations remain in the dedicated Research Agent documentation.

## Phase 14 — Project0 Agent Skills Foundation

### Objective

Establish repository-local, reusable Agent Skills while preserving deterministic workflow enforcement.

### Delivered capability

- `skills/<skill-name>/SKILL.md` repository structure;
- immutable skill metadata and loaded-definition models;
- deterministic discovery, validation, and loading;
- active-skill propagation through Reasoning Requests;
- skill instructions and metadata in provider prompts;
- Platform Dispatcher Skill Registry assembly;
- source-grounded Documentation Workflow selection of `strict-documentation-editor`; and
- skill-related unit and integration test source.

### Current boundaries

The Research Workflow does not receive or select from the shared Skill Registry. External skill discovery, installation, trust validation, approval, version management, and remote distribution are not implemented. Skills guide model behavior; deterministic workflow policy remains in Python.

## 4. Dependency Direction

The implemented dependency direction is:

1. repository configuration and startup validation;
2. shared models and protocol interfaces;
3. repository, context, knowledge, reasoning-provider, artifact, skill, and validation services;
4. generic and agent-specific workflow coordinators;
5. Platform Dispatcher composition;
6. agent UI services and routers; and
7. Dashboard application composition and presentation.

Key sequencing principles are:

- repository access before repository analysis;
- deterministic context/knowledge selection before source-grounded reasoning;
- provider-neutral reasoning boundaries before agent-specific model use;
- validation and controlled-update services before applying reviewed changes;
- shared Dashboard infrastructure before agent UI integration; and
- deterministic platform/agent testing before live-provider validation.

Agent workflows can depend on shared platform services. Shared platform services should not acquire agent-specific UI or domain responsibilities.

## 5. Verification Strategy

Verification is continuous and layered:

- focused unit tests for services, models, providers, routes, registries, and workflows;
- integration tests for real assembled component boundaries;
- browser acceptance tests for externally observable Dashboard-hosted behavior;
- strict documentation builds;
- source-compilation checks;
- optional live-provider and runtime checks separated from deterministic regression; and
- final source, documentation, and roadmap/status consistency review.

Results must identify the exact source state and environment. Historical counts cannot establish the status of a later commit. Skips, unavailable tools, environment limitations, and failures must be reported rather than converted into implied success.

## 6. Current Corrective Priorities

The following work is supported by verified repository gaps at commit `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`:

1. Remove Markdown fences from `src/project0/interfaces/knowledge_interfaces.py` and restore clean source compilation.
2. Decide whether Documentation Consistency belongs in the default Documentation Workflow validator tuple; then align implementation, tests, and documentation.
3. Replace or derive the Dashboard's hard-coded project-phase label from an authoritative status source.
4. Declare the browser acceptance dependencies and browser-installation procedure, or maintain a clearly separate supported acceptance environment.
5. Add substantive tests to effectively empty test modules or remove placeholders that imply coverage.
6. Re-run Python compilation, the complete pytest suite, and `mkdocs build --strict` against the corrected commit and record the exact result.
7. Add continuous integration only after its supported environment and required gates are defined.

These corrective items improve the current baseline; they are not evidence that the corresponding phases were absent.

## 7. Roadmap Success Criteria

The current Project0 baseline is considered verified only when:

- implemented component interfaces operate according to their typed contracts;
- deterministic platform, Documentation, and Research workflows pass their applicable tests;
- repository-writing workflows preserve human review and safety constraints;
- browser interfaces pass applicable acceptance scenarios in a supported environment;
- documentation validation and source compilation complete without errors;
- current status and test-result documents identify the validated commit and environment;
- known gaps are resolved or explicitly accepted as limitations; and
- implemented behavior remains aligned across source, tests, configuration, templates, and documentation.

These are repository-wide verification criteria, not a claim that they were satisfied by the pinned audit commit.

## 8. Future Expansion

Potential future work, not current capability or a committed schedule:

- semantic, embedding, or vector-based repository retrieval;
- durable workflow, review, and audit storage;
- asynchronous or distributed workflows;
- additional reasoning providers;
- expanded validation, security, and static analysis;
- performance and benchmark testing;
- additional specialized agents;
- shared Research Agent skill selection;
- external Agent Skill trust, approval, installation, and lifecycle management;
- dynamic plugin and agent registration;
- authentication and role-based access;
- deployment automation; and
- CI/CD workflows.

Future phases should be added only when scope, ownership, dependencies, deliverables, and validation criteria are sufficiently defined.
