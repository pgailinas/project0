# Project Directory Structure

**Version:** 0.3  
**Owner:** Project0  
**Last Updated:** 2026-08-06

---
# Overview

This document describes the Project0 repository organization and the
purpose of each major directory within the project.

Project0 is organized as a documentation-first software development
platform. The repository contains the complete project documentation,
implementation source code, testing infrastructure, project tracking
artifacts, and supporting resources required to develop and maintain the
Documentation Agent.

The repository serves as the authoritative source for all project
documentation, implementation, automated testing, and supporting artifacts.

---
# Repository Structure

``` text
project0/
├── docs/
│   ├── index.md
│   ├── Project_Directory_Structure.md
│   ├── 01_Project_Charter.md
│   ├── 02_Documentation_Standards.md
│   ├── 03_Documentation_Agent_Functional_Specification.md
│   ├── 04_Documentation_Agent_Architecture.md
│   ├── 05_Documentation_Agent_Component_Design.md
│   ├── 06_Implementation_Roadmap.md
│   ├── 07_Implementation_Status.md
│   ├── 07_Implementation_Status.ods
│   ├── Testing_Guide.md
│   ├── Dashboard_Design.md
│   ├── Documentation_Agent_Interface_Design.md
│   ├── images/
│   ├── assets/
│   └── javascripts/
│       └── mermaid.js
├── src/
│   └── project0/
│       ├── common/
│       ├── config/
│       ├── dashboard/
│       │   ├── dashboard_app.py
│       │   └── dashboard_routes.py
│       │   └── templates/
│       │   │   ├── dashboard.html
│       │   │   └── dashboard_home.html
│       │   └── css/
│       │       └── dashboard.css
│       ├── interfaces/
│       │   ├── documentation_workflow_interfaces.py
│       │   └── validation_interfaces.py
│       ├── knowledge/
│       ├── models/
│       │   ├── documentation_workflow_models.py
│       │   └── validation_models.py
│       ├── platform/
│       ├── reasoning/
│       ├── repository/
│       │   ├── git_diff_service.py
│       │   └── repository_update_service.py
│       ├── validation/
│       │   ├── documentation_consistency_validator.py
│       │   ├── link_validator.py
│       │   ├── markdown_validator.py
│       │   ├── mkdocs_validator.py
│       │   └── validation_service.py
│       └── workflow/
│           ├── documentation_workflow.py
│           └── review_coordinator.py
├── tests/
│   ├── integration/
│   │   ├── test_context_builder_flow.py
│   │   ├── test_core_platform_flow.py
│   │   ├── test_dashboard_flow.py
│   │   ├── test_documentation_workflow_flow.py
│   │   ├── test_knowledge_service_flow.py
│   │   ├── test_platform_dispatcher_flow.py
│   │   ├── test_reasoning_service_flow.py
│   │   └── test_validation_service_flow.py
│   └── unit/
│       ├── common/
│       ├── config/
│       ├── dashboard/
│       ├── knowledge/
│       ├── models/
│       ├── platform/
│       ├── reasoning/
│       ├── repository/
│       ├── validation/
│       └── workflow/
├── scripts/
├── mkdocs.yml
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

## Repository Directory Purposes

| Directory | Purpose |
|-----------|---------|
| `docs/` | Project documentation, GitHub Pages source, implementation roadmap, implementation status, supporting assets, and companion spreadsheets. |
| `src/` | Python implementation of the Project0 platform organized into reusable architectural services, the Dashboard Framework, platform services, interfaces, workflows, models, repository services, validation services, reasoning services, and future AI agents. |
| `tests/` | Unit and integration tests organized by architectural component and workflow validation. |
| `scripts/` | Development and automation scripts. |
| `README.md` | GitHub repository landing page. |
| `mkdocs.yml` | Material for MkDocs configuration. |
| `pyproject.toml` | Python project configuration and dependencies. |

---
# Relationship Between Documentation and Implementation

Implementation within `src/` follows the project architecture. Material for MkDocs generates the GitHub Pages website directly from the Markdown documents stored in `docs/`. The generated HTML is a published representation of the documentation and is not the authoritative source.

The Dashboard Framework is implemented within the `src/project0/dashboard/` package and provides the reusable browser-based user interface used by Project0 services and future AI agents.

---

# Important Notes

- The GitHub repository is the authoritative source for Project0 documentation and implementation.
- Markdown (`.md`) is the authoritative documentation format.
- Companion OpenDocument Spreadsheet (`.ods`) files provide structured project tracking.
- GitHub Pages documentation is generated from the `docs/` directory using Material for MkDocs.
- The Project0 Dashboard Framework provides the reusable browser-based user interface for the Project0 platform.
- Individual AI agents inherit the Dashboard Framework while implementing their own pages, workflows, and business logic independently.
