# Project Directory Structure

**Version:** 0.2  
**Owner:** Project0  
**Last Updated:** 2026-08-04

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
documentation, implementation, and supporting artifacts.

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
│   ├── images/
│   ├── assets/
│   └── javascripts/
│       └── mermaid.js
├── src/
│   └── project0/
│       ├── common/
│       ├── config/
│       ├── interfaces/
│       ├── knowledge/
│       ├── models/
│       ├── platform/
│       ├── reasoning/
│       ├── validation/
│       ├── workflow/
│       └── main.py
├── tests/
│   ├── integration/
│   └── unit/
│       ├── common/
│       ├── config/
│       ├── knowledge/
│       ├── models/
│       ├── platform/
│       ├── reasoning/
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
| `src/` | Python implementation of the Documentation Agent organized by architectural component. |
| `tests/` | Unit, integration, and end-to-end testing. |
| `scripts/` | Development and automation scripts. |
| `README.md` | GitHub repository landing page. |
| `mkdocs.yml` | Material for MkDocs configuration. |
| `pyproject.toml` | Python project configuration and dependencies. |

---
# Relationship Between Documentation and Implementation

Implementation within `src/` follows the project architecture. Material
for MkDocs generates the GitHub Pages website directly from the Markdown
documents stored in `docs/`. The generated HTML is a published
representation of the documentation and is not the authoritative source.

---
# Important Notes

-   The GitHub repository is the authoritative source for Project0
    documentation and implementation.
-   Markdown (`.md`) is the authoritative documentation format.
-   Companion OpenDocument Spreadsheet (`.ods`) files provide structured
    project tracking.
-   GitHub Pages documentation is generated from the `docs/` directory
    using Material for MkDocs.
