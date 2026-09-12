# Project0

Project0 is a documentation-first, AI-native software development platform for building, validating, and maintaining AI-assisted software systems through modular architecture, controlled workflows, shared platform services, and comprehensive project documentation.

The platform is designed around specialized AI agents that reuse common services while keeping agent-specific behavior, workflows, interfaces, and validation clearly separated.

## Documentation

The published Project0 documentation is available at:

- **Project0 Documentation:** https://pgailinas.github.io/project0/
- **Project Documentation:** https://pgailinas.github.io/project0/project/
- **Platform Documentation:** https://pgailinas.github.io/project0/platform/
- **Documentation Agent Documentation:** https://pgailinas.github.io/project0/agents/documentation/
- **Research Agent Documentation:** https://pgailinas.github.io/project0/agents/research/

The documentation site is the preferred entry point for architecture, design, implementation status, testing, validation, and agent-specific details.

## Current Capabilities

Project0 currently includes:

- a shared FastAPI/Jinja2 browser Dashboard;
- reusable configuration, repository, context, reasoning, validation, and workflow services;
- provider-neutral reasoning with local Ollama support;
- repository-local Agent Skills;
- controlled documentation-update workflows;
- multi-source research workflows;
- shared System Status reporting for active agents;
- live Research Agent workflow-stage reporting; and
- project-wide automated tests and validation.

## Implemented Agents

### Documentation Agent

The Documentation Agent supports controlled, source-grounded documentation maintenance.

Current capabilities include:

- documentation-change requests;
- explicit ground-truth source and target paths;
- strict-mode source analysis;
- minimal proposed documentation changes;
- deterministic validation;
- human review and approval;
- controlled application of approved changes; and
- final validation and Git-diff review.

Documentation:

https://pgailinas.github.io/project0/agents/documentation/

### Research Agent

The Research Agent supports structured research discovery, evaluation, analysis, and synthesis.

Current capabilities include:

- optional existing-research context ingestion;
- research-question and guidance input;
- bounded research-strategy generation;
- multi-source literature discovery;
- metadata retrieval and normalization;
- relevance scoring and ranking;
- structured paper analysis;
- research-direction synthesis;
- downloadable Markdown research results;
- live backend-driven workflow progress; and
- synchronized System Status reporting.

Documentation:

https://pgailinas.github.io/project0/agents/research/

## Research Workflow

The Research Agent currently reports the following live workflow stages:

1. Request
2. Strategy
3. Source Search
4. Metadata
5. Evaluation
6. Artifacts
7. Complete

The Dashboard reflects the active backend stage rather than simulating progress in the browser.

## Quick Start

Install Project0 in editable mode with test dependencies:

```bash
python -m pip install -e '.[test]'
```

A typical local development configuration uses Ollama for reasoning:

```bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_DOCUMENTATION_OLLAMA_MODEL=qwen2.5:7b
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=openalex,crossref,arxiv,openreview
export PROJECT0_LOG_LEVEL=DEBUG
```

Start the Dashboard:

```bash
python -m project0.dashboard.dashboard_app
```

Then open:

```text
http://127.0.0.1:8001
```

The Dashboard provides access to:

- Project Overview
- Documentation Agent
- Research Agent
- Project and agent documentation entry points

## Testing

Run the full automated test suite with:

```bash
python -m pytest
```

Project0 uses unit and integration tests to validate shared platform services, agent behavior, Dashboard routes, workflows, and UI flows.

For current verification details, see:

https://pgailinas.github.io/project0/platform/Project0_Validation_Status/

## Documentation Structure

Repository documentation is organized into four primary areas:

```text
docs/
├── index.md
├── project/
│   └── index.md
├── platform/
│   └── index.md
└── agents/
    ├── documentation/
    │   └── index.md
    └── research/
        └── index.md
```

Each documentation area has an overview page that links to its detailed design, architecture, testing, status, and validation documents.

## Development Principles

Project0 development emphasizes:

- documentation as a first-class, version-controlled artifact;
- source code, tests, templates, and configuration as the authority for implemented behavior;
- deterministic processing where model reasoning is unnecessary;
- bounded and reviewable AI-assisted workflows;
- explicit separation between shared platform behavior and agent-specific behavior;
- human approval for controlled documentation changes;
- small, coherent implementation changes;
- validation before changes are treated as complete; and
- synchronized source, tests, and documentation.

## Project Scope

Project0 is currently a local-first development platform. It is intended as a reusable foundation for additional specialized agents and AI-assisted software-development workflows.

Current work focuses on strengthening the shared platform, Documentation Agent, Research Agent, Dashboard, testing, validation, and documentation before expanding into additional agents and deployment models.

## Source of Truth

The Project0 source repository is the implementation source of truth.

Documentation should remain synchronized with implemented source code, tests, templates, and configuration, and should avoid claims that are not supported by the repository.
