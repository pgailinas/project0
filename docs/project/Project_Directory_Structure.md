# Project Directory Structure

**Version:** 0.7  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## Overview

Project0 is organized as a documentation-first AI-native software development
platform. The repository contains authoritative Markdown documentation,
reusable platform code, specialized agent packages, repository-local skills,
and unit, integration, and browser acceptance tests.

This page describes the current high-level structure. It intentionally omits
generated caches and individual files outside the areas needed to understand
the architecture.

---

## Repository Structure

~~~text
project0/
├── docs/
│   ├── index.md
│   ├── agents/
│   │   ├── documentation/
│   │   │   ├── Documentation_Agent_Charter.md
│   │   │   ├── Documentation_Agent_Functional_Spec.md
│   │   │   ├── Documentation_Agent_Architecture.md
│   │   │   ├── Documentation_Agent_Design.md
│   │   │   ├── Documentation_Agent_Interface_Design.md
│   │   │   ├── Documentation_Agent_Testing_Guide.md
│   │   │   ├── Documentation_Agent_Test_Plan.md
│   │   │   └── Documentation_Agent_Test_Results.md
│   │   └── research/
│   │       ├── Research_Agent_Charter.md
│   │       ├── Research_Agent_Functional_Spec.md
│   │       ├── Research_Agent_Architecture.md
│   │       ├── Research_Agent_Design.md
│   │       ├── Research_Agent_Interface_Design.md
│   │       ├── Research_Agent_Testing_Guide.md
│   │       ├── Research_Agent_Test_Plan.md
│   │       └── Research_Agent_Test_Results.md
│   ├── platform/
│   │   ├── Agent_Skills_Design.md
│   │   ├── Component_Communication_Design.md
│   │   ├── Dashboard_Design.md
│   │   ├── Project0_Test_Results.md
│   │   └── Shared_Data_Models_and_Error_Contracts.md
│   └── project/
│       ├── Development_Environment.md
│       ├── Development_Standards.md
│       ├── Documentation_Standards.md
│       ├── Implementation_Roadmap.md
│       ├── Implementation_Status.md
│       ├── Project_Charter.md
│       ├── Project_Directory_Structure.md
│       └── Testing_Guide.md
├── skills/
│   └── strict-documentation-editor/
│       └── SKILL.md
├── src/project0/
│   ├── agents/
│   │   ├── documentation/
│   │   │   ├── css/
│   │   │   ├── templates/
│   │   │   ├── documentation_agent_routes.py
│   │   │   ├── documentation_agent_ui_service.py
│   │   │   └── documentation_agent_view_models.py
│   │   └── research/
│   │       ├── css/
│   │       ├── templates/
│   │       ├── *_source_provider.py
│   │       ├── existing_research_context_analysis_service.py
│   │       ├── paper_analysis_service.py
│   │       ├── paper_metadata_service.py
│   │       ├── research_agent_routes.py
│   │       ├── research_agent_ui_service.py
│   │       ├── research_agent_view_models.py
│   │       ├── research_artifact_service.py
│   │       ├── research_context_ingestion_service.py
│   │       ├── research_direction_analysis_service.py
│   │       ├── research_evaluation_service.py
│   │       ├── research_query_service.py
│   │       ├── research_source_provider.py
│   │       ├── research_source_provider_factory.py
│   │       ├── research_source_service.py
│   │       └── research_strategy_service.py
│   ├── artifacts/
│   ├── common/
│   ├── config/
│   ├── dashboard/
│   │   ├── css/
│   │   ├── templates/
│   │   ├── dashboard_app.py
│   │   └── dashboard_routes.py
│   ├── interfaces/
│   ├── knowledge/
│   ├── models/
│   ├── platform/
│   ├── reasoning/
│   ├── repository/
│   ├── validation/
│   └── workflow/
│       ├── documentation_workflow.py
│       └── research_workflow.py
├── tests/
│   ├── unit/
│   │   ├── agents/
│   │   │   ├── documentation/
│   │   │   └── research/
│   │   ├── config/
│   │   ├── dashboard/
│   │   ├── models/
│   │   ├── platform/
│   │   ├── reasoning/
│   │   └── workflow/
│   ├── integration/
│   │   ├── agents/
│   │   │   ├── documentation/
│   │   │   └── research/
│   │   └── platform/
│   ├── acceptance/
│   │   ├── agents/
│   │   │   ├── documentation/
│   │   │   └── research/
│   │   └── platform/
│   └── test_data/
├── mkdocs.yml
├── pyproject.toml
├── README.md
├── TEST_COMMANDS.md
└── .gitignore
~~~

---

## Directory Purposes

| Directory | Purpose |
| --- | --- |
| `docs/` | Authoritative Markdown for the MkDocs site and project review. |
| `docs/agents/research/` | Research Agent charter, functional, architecture, design, interface, testing, plan, and result records. |
| `skills/` | Repository-local Agent Skills loaded by the Project0 Skill Registry. |
| `src/project0/agents/research/` | Research-specific providers, services, routes, views, template, and CSS. |
| `src/project0/platform/` | Shared composition and dispatch, including Research Workflow assembly. |
| `src/project0/models/` | Shared immutable models, including Research and Reasoning models. |
| `src/project0/interfaces/` | Shared service/workflow protocols. |
| `src/project0/workflow/` | Documentation and Research workflow orchestration. |
| `src/project0/dashboard/` | Shared FastAPI application, shell, status endpoints, templates, and CSS. |
| `tests/unit/agents/research/` | Isolated Research Agent component tests. |
| `tests/integration/agents/research/` | Assembled workflow and UI integration tests. |
| `tests/acceptance/agents/research/` | Playwright Research Agent browser scenarios. |

---

## Research Agent Source Boundaries

Research-specific business logic belongs under
`src/project0/agents/research/`. The complete workflow coordinator resides at
`src/project0/workflow/research_workflow.py`, shared models at
`src/project0/models/research_models.py`, and protocols at
`src/project0/interfaces/research_interfaces.py`.

The shared Dashboard application registers Research Agent routes and provides
the shell/status endpoint. The shared Platform Dispatcher assembles the
Research Workflow. The reusable Markdown/Link/MkDocs Validation Service is
used by documentation workflows, not by the Research Workflow.

---

## Documentation and Generated Output

Markdown under `docs/` is authoritative for published documentation. Generated
MkDocs output, when present locally, is not authoritative.

Research Agent result output has two separate forms:

- in-memory compatibility `ResearchArtifact` values returned by the workflow;
  and
- `project0_research_results.md` generated by the browser's **Save Results**
  action.

Neither form is automatically written into the repository.

---

## Important Notes

- The current Research Agent unit, integration, and acceptance directories are
  implemented; they are not planned placeholders.
- The source tree contains separate Documentation and Research Agent packages.
- The private repository source, tests, configuration, and templates are the
  implementation authority. Generated GitHub Pages content is not.
- Individual agents own their Work Area behavior while the Dashboard owns the
  shared shell and status presentation.

