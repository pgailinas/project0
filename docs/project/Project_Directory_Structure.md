# Project Directory Structure

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-08-10

---
## Overview

Project0 is organized as a documentation-first AI-native software development
platform. The repository contains project documentation, reusable platform
implementation, AI agent implementations, testing infrastructure, project
tracking artifacts, and supporting resources required to develop and maintain
Project0 and its specialized AI agents.

The repository serves as the authoritative source for all project
documentation, implementation, automated testing, and supporting artifacts.

---
## Repository Structure

``` text
project0/
├── docs/
│   │
│   ├── index.md
│   │
│   ├── project/
│   │   ├── Project_Charter.md
│   │   ├── Development_Environment.md
│   │   ├── Testing_Guide.md
│   │   ├── Documentation_Standards.md
│   │   ├── Project_Directory_Structure.md
│   │   ├── Implementation_Roadmap.md
│   │   ├── Implementation_Status.md
│   │   ├── Implementation_Status.ods
│   │   └── Implementation_Status.pdf
│   │
│   ├── platform/
│   │   ├── Dashboard_Design.md
│   │   ├── Component_Communication_Design.md
│   │   ├── Shared_Data_Models_and_Error_Contracts.md
│   │   ├── Project0_Test_Plan.md
│   │   └── Project0_Test_Results.md
│   │
│   └── agents/
│       │
│       ├── documentation/
│       │   ├── Documentation_Agent_Charter.md
│       │   ├── Documentation_Agent_Functional_Spec.md
│       │   ├── Documentation_Agent_Architecture.md
│       │   ├── Documentation_Agent_Design.md
│       │   ├── Documentation_Agent_Interface_Design.md
│       │   ├── Documentation_Agent_Testing_Guide.md
│       │   ├── Documentation_Agent_Test_Plan.md
│       │   └── Documentation_Agent_Test_Results.md
│       │
│       └── research/ (planned)
│           ├── Research_Agent_Charter.md (planned)
│           ├── Research_Agent_Functional_Spec.md (planned)
│           ├── Research_Agent_Architecture.md (planned)
│           ├── Research_Agent_Design.md (planned)
│           ├── Research_Agent_Interface_Design.md (planned)
│           ├── Research_Agent_Testing_Guide.md (planned)
│           ├── Research_Agent_Test_Plan.md (planned)
│           └── Research_Agent_Test_Results.md (planned)
│
├── src/
│   │
│   └── project0/
│       ├── agents/
│       │   └── documentation/
│       │       ├── templates/
│       │       └── css/
│       ├── common/
│       ├── config/
│       ├── dashboard/
│       │   ├── templates/
│       │   └── css/
│       ├── interfaces/
│       ├── knowledge/
│       ├── models/
│       ├── platform/
│       ├── reasoning/
│       ├── repository/
│       ├── validation/
│       └── workflow/
│
├── tests/
│   │
│   ├── unit/
│   │   ├── agents/
│   │   │   ├── documentation/
│   │   │   └── research/ (planned)
│   │   ├── common/
│   │   ├── config/
│   │   ├── dashboard/
│   │   ├── knowledge/
│   │   ├── models/
│   │   ├── platform/
│   │   ├── reasoning/
│   │   ├── repository/
│   │   ├── validation/
│   │   └── workflow/
│   │
│   ├── integration/
│   │   ├── platform/
│   │   └── agents/
│   │
│   └── acceptance/
│       ├── platform/
│       └── agents/
│           ├── documentation/
│           └── research/ (planned)
│
├── mkdocs.yml
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

### Repository Directory Purposes

| Directory | Purpose |
|-----------|---------|
| `docs/` | Authoritative Markdown documentation organized into Project0-wide, reusable platform, and agent-specific documentation, and used as the source for GitHub Pages. |
| `src/` | Python implementation of reusable Project0 platform services, the Dashboard Framework, shared infrastructure, and specialized AI agents. |
| `tests/` | Automated verification organized into unit, integration, and acceptance tests covering reusable platform services, AI agent behavior, user workflows, and system-level validation. |
| `README.md` | GitHub repository landing page. |
| `mkdocs.yml` | Material for MkDocs configuration. |
| `pyproject.toml` | Python project configuration and dependencies. |

---
## Relationship Between Documentation and Implementation

Implementation within `src/` follows the project architecture. Material for MkDocs generates the GitHub Pages website directly from the Markdown documents stored in `docs/`. The generated HTML is a published representation of the documentation and is not the authoritative source.

Automated acceptance tests are organized separately from implementation code and verify complete user-facing workflows, platform capabilities, and agent behavior using the contracts defined by the platform and agent architectures.

The Dashboard Framework is implemented within the `src/project0/dashboard/` package and provides the reusable browser-based user interface used by Project0 services and future AI agents.

Project0 separates reusable platform documentation and implementation from agent-specific documentation and implementation. Platform documentation is stored under `docs/platform/`, while agent-specific documentation is stored
under `docs/agents/<agent>/`. Correspondingly, reusable platform source remains within the applicable `src/project0/` service packages, while agent-specific source is located under `src/project0/agents/<agent>/`.

---

## Important Notes

- The GitHub repository is the authoritative source for Project0 documentation and implementation.
- Markdown (`.md`) is the authoritative documentation format.
- Companion OpenDocument Spreadsheet (`.ods`) files provide structured project tracking.
- GitHub Pages documentation is generated from the `docs/` directory using Material for MkDocs.
- The Project0 Dashboard Framework provides the reusable browser-based user interface for the Project0 platform.
- Individual AI agents integrate with the Dashboard Framework while implementing their own Work Area interactions, workflows, and business logic independently.

