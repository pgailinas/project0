# Welcome to Project0

## AI-Native Software Development Platform

Project0 is a local-first, documentation-centered Python platform for building, evaluating, and maintaining specialized AI-assisted workflows. The current repository combines deterministic repository, context, knowledge, validation, and workflow services with provider-neutral reasoning, human-reviewed documentation updates, evidence-aware research workflows, repository-local Agent Skills, and a shared browser Dashboard.

Executable source, tests, templates, and configuration are authoritative for implemented behavior. Markdown records design, contracts, usage, plans, status, and results and must remain synchronized as the implementation changes.

## Project Goals

Project0 aims to:

- provide reusable infrastructure for specialized AI agents;
- support coordinated AI-assisted software-engineering workflows;
- preserve human authority through explicit review and approval boundaries;
- reuse shared services for repository access, context, knowledge, reasoning, validation, workflow execution, skills, and presentation;
- provide a consistent browser Dashboard for platform and agent interfaces;
- keep reusable platform responsibilities separate from agent-specific behavior;
- prefer deterministic processing whenever model reasoning is unnecessary; and
- serve as a practical foundation for additional agents and development capabilities.

## Current Architecture at a Glance

Project0 is organized into distinct responsibility layers:

| Layer | Current role |
| --- | --- |
| Configuration and common services | Environment settings, logging, and startup validation |
| Shared models and protocols | Typed requests, results, state, value objects, and substitutable interfaces |
| Repository, context, and knowledge | Safe repository access, deterministic context construction, Markdown parsing, selection, and formatting |
| Reasoning and providers | Provider-neutral prompts/results with Ollama and deterministic stub implementations |
| Validation and artifacts | Markdown/link/MkDocs/consistency validation plus controlled artifact locations and updates |
| Workflow coordination | Generic task execution plus separate Documentation and Research workflow coordinators |
| Platform composition | Service and workflow assembly through `PlatformDispatcher` |
| Dashboard and agent interfaces | Shared FastAPI/Jinja2 shell with agent-owned routes, UI services, view models, templates, and styles |

The generic Workflow Engine currently executes generic task lists and the context workflow. `PlatformDispatcher` invokes the stateful Documentation Workflow and the Research Workflow directly; neither agent workflow is converted into a generic task list.

## Documentation

### Project

| Document | Purpose |
| --- | --- |
| [Project Charter](project/Project_Charter.md) | Project vision, scope, principles, stakeholders, and intended outcomes |
| [Project Directory Structure](project/Project_Directory_Structure.md) | Repository organization, package ownership, and dependency boundaries |
| [Development Environment](project/Development_Environment.md) | Installation, runtime configuration, startup, tools, and troubleshooting |
| [Development Standards](project/Development_Standards.md) | Engineering, implementation, validation, review, and AI-collaboration standards |
| [Documentation Standards](project/Documentation_Standards.md) | Documentation ownership, structure, source-grounding, and publishing conventions |
| [Testing Guide](project/Testing_Guide.md) | Test layers, environment, commands, dependencies, naming, and reporting rules |
| [Implementation Roadmap](project/Implementation_Roadmap.md) | Phase 1–14 history, delivered capabilities, boundaries, corrective work, and future expansion |
| [Implementation Status](project/Implementation_Status.md) | Current implementation matrix, verification state, gaps, and operational limits |

### Platform

| Document | Purpose |
| --- | --- |
| [Dashboard Design](platform/Dashboard_Design.md) | Shared FastAPI shell, routes, layout, status presentation, and agent registration |
| [Component Communication Design](platform/Component_Communication_Design.md) | Runtime composition, service interactions, workflow boundaries, events, and failure propagation |
| [Shared Data Models and Error Contracts](platform/Shared_Data_Models_and_Error_Contracts.md) | Implemented model families, status values, repository errors, and boundary-specific failure behavior |
| [Agent Skills Design](platform/Agent_Skills_Design.md) | Repository-local skill format, immutable models, registry behavior, reasoning integration, and limits |
| [Project0 Validation Status](platform/Project0_Validation_Status.md) | Commit-specific regression/validation record and historical-result boundary |

### Documentation Agent

| Document | Purpose |
| --- | --- |
| [Documentation Agent Charter](agents/documentation/Documentation_Agent_Charter.md) | Mission, scope, operating principles, authority, and success criteria |
| [Documentation Agent Functional Specification](agents/documentation/Documentation_Agent_Functional_Spec.md) | Required capabilities, inputs, outputs, constraints, and workflows |
| [Documentation Agent Architecture](agents/documentation/Documentation_Agent_Architecture.md) | High-level components, dependencies, state, and workflow architecture |
| [Documentation Agent Design](agents/documentation/Documentation_Agent_Design.md) | Detailed service responsibilities, behavior, and integration |
| [Documentation Agent Interface Design](agents/documentation/Documentation_Agent_Interface_Design.md) | UI and service contracts, review boundaries, and platform integration |
| [Documentation Agent Testing Guide](agents/documentation/Documentation_Agent_Testing_Guide.md) | Agent-specific test commands, environment, workflow validation, and troubleshooting |
| [Documentation Agent Test Plan](agents/documentation/Documentation_Agent_Test_Plan.md) | Agent requirements mapped to unit, integration, acceptance, safety, and provider scenarios |
| [Documentation Agent Test Results](agents/documentation/Documentation_Agent_Test_Results.md) | Recorded agent test executions, outcomes, issues, and evidence limits |

### Research Agent

| Document | Purpose |
| --- | --- |
| [Research Agent Charter](agents/research/Research_Agent_Charter.md) | Mission, scope, evidence principles, authority, and success criteria |
| [Research Agent Functional Specification](agents/research/Research_Agent_Functional_Spec.md) | Required retrieval, analysis, evaluation, synthesis, and artifact behavior |
| [Research Agent Architecture](agents/research/Research_Agent_Architecture.md) | High-level services, providers, workflows, evidence flow, and dependencies |
| [Research Agent Design](agents/research/Research_Agent_Design.md) | Detailed component responsibilities, algorithms, boundaries, and results |
| [Research Agent Interface Design](agents/research/Research_Agent_Interface_Design.md) | Request/results UI contracts, view models, routes, and Dashboard integration |
| [Research Agent Testing Guide](agents/research/Research_Agent_Testing_Guide.md) | Agent-specific commands, live/stub configuration, expected bounds, and troubleshooting |
| [Research Agent Test Plan](agents/research/Research_Agent_Test_Plan.md) | Unit, integration, browser, live-provider, safety, grounding, and regression coverage |
| [Research Agent Test Results](agents/research/Research_Agent_Test_Results.md) | Recorded Research validation coverage, execution evidence, and verification limits |

Agent-specific workflow, model, UI, and test semantics belong in these dedicated sets. Project and platform documents describe only shared composition, contracts, practices, status, and boundaries.

## Implemented Platform Capabilities

The shared platform currently provides:

- safe repository-relative discovery and UTF-8 text reads;
- deterministic documentation Context Builder and in-memory Markdown Knowledge Service;
- generic synchronous sequential task execution with optional lifecycle event publication;
- provider-neutral reasoning with Ollama and deterministic stub providers;
- Markdown, local-link, strict MkDocs, and documentation-consistency validators;
- controlled, human-reviewed Markdown updates and Git diff generation;
- repository-local Agent Skill discovery, validation, loading, and reasoning-prompt integration;
- FastAPI/Jinja2 Dashboard composition, shared routes, sidebar status, and agent extension points; and
- registered Documentation and Research agent interfaces.

The Documentation Agent includes source-grounded proposal generation, human review, controlled updates, validation, and completion reporting. The Research Agent includes multi-provider literature retrieval, optional existing-context processing, paper evidence and analysis, evaluation, synthesis, and evidence-grounded Research Direction Analysis.

Detailed capability claims and verification evidence remain in the owning documents rather than this landing page.

## Current Runtime

Install Project0 in editable mode with its declared test dependencies:

```bash
python -m pip install -e '.[test]'
```

The repository provides two application entry paths:

```bash
python -m project0.main
python -m project0.dashboard.dashboard_app
```

`project0.main` validates required repository structure and executes one general documentation-context workflow through the generic Workflow Engine. It does not start an interactive agent.

`project0.dashboard.dashboard_app` starts the executable FastAPI Dashboard on `http://127.0.0.1:8001` with both agent interfaces registered.

Serve the documentation separately:

```bash
mkdocs serve
```

The Dashboard's `/documentation` route redirects to `http://127.0.0.1:8000`, the default local MkDocs address. The Dashboard does not start or host MkDocs.

## Configuration Summary

Default Dashboard reasoning uses a local Ollama service and `qwen2.5:7b` unless model settings override it. The principal controls are:

- `PROJECT0_REASONING_PROVIDER`
- `PROJECT0_OLLAMA_MODEL`
- `PROJECT0_RESEARCH_OLLAMA_MODEL`
- `PROJECT0_DOCUMENTATION_OLLAMA_MODEL`
- `PROJECT0_OLLAMA_BASE_URL`
- `PROJECT0_OLLAMA_TIMEOUT_SECONDS`
- `PROJECT0_RESEARCH_SOURCE_PROVIDERS`
- `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS`

`PROJECT0_REASONING_PROVIDER=stub` selects deterministic Dashboard reasoning behavior. Default Research sources are `semantic_scholar,arxiv`; supported configured source names are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`.

See [Development Environment](project/Development_Environment.md) for exact defaults, credential variables, requirements, and troubleshooting.

## Development Principles

- Treat documentation as a first-class, version-controlled project artifact.
- Treat implemented source, tests, templates, and configuration as authority for current behavior.
- Prefer deterministic processing wherever model reasoning is unnecessary.
- Keep model guidance separate from deterministic workflow enforcement.
- Preserve human approval before Documentation Workflow changes are applied.
- Communicate through explicit typed interfaces and shared models.
- Keep shared platform services independent of agent-specific UI responsibilities.
- Make the smallest coherent change and update affected tests and documentation together.
- Tie completion and pass-count claims to the exact source state that was validated.

See [Development Standards](project/Development_Standards.md) and [Documentation Standards](project/Documentation_Standards.md) for the complete rules.

## Current Status and Boundaries

The latest named roadmap phase is Phase 14 — Project0 Agent Skills Foundation. Source corresponding to Phases 1–14 exists, including the Phase 12 Documentation Agent enhancements omitted from the older status list. Repository-wide verification is incomplete at the pinned audit commit.

Not implemented as shared platform capabilities:

- durable workflow, review, research-session, or audit storage;
- asynchronous or distributed workflow execution;
- automatic Git commit, push, pull request, publication, or deployment;
- continuous-integration or deployment workflows;
- authentication or role-based access;
- external Agent Skill installation and trust management;
- semantic/vector repository retrieval; and
- dynamic configuration-only agent registration.

The Dashboard `/activity` and `/settings` entries are navigation placeholders. The shared project-phase label displayed by the Dashboard is hard-coded to an earlier phase and is not an authoritative current-status source.

## Verification Status

This documentation synchronization is pinned to commit `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`.

- Pytest was unavailable in the audit environment, so no current regression count was established.
- MkDocs was unavailable, so no current strict documentation-build result was established.
- `python -m compileall -q src` failed because `src/project0/interfaces/knowledge_interfaces.py` contains Markdown code fences around the Python module.
- The historical `1265 passed, 11 skipped` record from 2026-09-09 was not tied to the pinned commit and does not establish its status.

See [Implementation Status](project/Implementation_Status.md), [Testing Guide](project/Testing_Guide.md), and [Project0 Validation Status](platform/Project0_Validation_Status.md) for the precise status, commands, gaps, and reporting rules.

## Getting Started

1. Read the [Project Charter](project/Project_Charter.md) for vision and scope.
2. Configure the [Development Environment](project/Development_Environment.md).
3. Review the [Development Standards](project/Development_Standards.md) and [Documentation Standards](project/Documentation_Standards.md).
4. Learn shared boundaries in [Component Communication Design](platform/Component_Communication_Design.md) and [Shared Data Models and Error Contracts](platform/Shared_Data_Models_and_Error_Contracts.md).
5. Use the [Testing Guide](project/Testing_Guide.md) before treating a change as verified.
6. Consult the dedicated Documentation or Research Agent set for agent-specific behavior.
7. Check [Implementation Status](project/Implementation_Status.md) and [Project0 Validation Status](platform/Project0_Validation_Status.md) before relying on a milestone or pass claim.

## Future Direction

Project0 can be extended with additional specialized agents and reusable capabilities for software architecture, design, implementation, testing, code review, project management, and multi-agent collaboration. Potential platform work also includes durable state, semantic repository retrieval, additional reasoning providers, external skill lifecycle management, authentication, dynamic registration, and CI/CD.

These are possible future directions, not implemented capabilities or committed schedules. New work should be added to the roadmap only when its ownership, dependencies, deliverables, and validation criteria are defined.
