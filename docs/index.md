# Project0 Documentation

## AI-Native Software Development Platform

Project0 is a local-first, documentation-centered Python platform for building, evaluating, and maintaining specialized AI-assisted workflows.

This documentation site is organized into three primary deliverables. Each deliverable has its own overview page and detailed supporting documents.

## Run Project0

Project0 can be run in Google Colab, allowing users to view and exercise
the Project0 Dashboard and agents using a Colab GPU without requiring a local
NVIDIA GPU.

[Open Project0 in Google Colab](https://colab.research.google.com/github/pgailinas/project0/blob/main/notebooks/Project0_Colab_Launcher.ipynb){ .md-button .md-button--primary }

For environment requirements and runtime details, see the
[Development Environment](platform/Development_Environment.md).

## Documentation Deliverables

### Project0 Platform

Project0 Platform documentation covers Project0 goals, repository structure, development practices, testing, roadmap, implementation status, the shared Dashboard Framework, component communication, common data models and error contracts, Agent Skills, and project-level validation status.

[Open Project0 Platform Documentation](platform/index.md)

### Documentation Agent

The Documentation Agent documentation covers source-grounded documentation maintenance, workflow behavior, interface design, strict-mode updates, testing, and validation.

[Open Documentation Agent Documentation](documentation-agent/index.md)

### Research Agent

The Research Agent documentation covers research requests, literature discovery, metadata retrieval, relevance evaluation, structured analysis, research-direction synthesis, workflow behavior, testing, and validation.

[Open Research Agent Documentation](research-agent/index.md)

## Project0 at a Glance

Project0 currently provides shared services for repository access, context construction, reasoning-provider integration, validation, workflow coordination, Agent Skills, and browser-based agent interfaces.

The implemented agents are:

- **Documentation Agent** — controlled, source-grounded documentation maintenance with review and validation.
- **Research Agent** — multi-source literature discovery, relevance evaluation, structured analysis, and research-direction synthesis.

Executable source, tests, templates, and configuration are authoritative for implemented behavior. Documentation should remain synchronized with the implementation.

## Getting Started

For a new Project0 user or developer:

1. To exercise Project0 without a local NVIDIA GPU, use the
   [Project0 Colab launcher](https://colab.research.google.com/github/pgailinas/project0/blob/main/notebooks/Project0_Colab_Launcher.ipynb).
2. Start with the [Project0 Platform Documentation](platform/index.md) for scope,
   environment, standards, testing, roadmap, current implementation status,
   shared architecture, and platform boundaries.
3. Use the appropriate agent documentation set for agent-specific behavior and
   workflows.
4. Check the relevant validation and test-results documents before relying on
   current-status or pass-count claims.

## Source of Truth

The Project0 source repository is the implementation source of truth. Documentation should describe verified current behavior and should avoid introducing architecture, capabilities, or status not supported by the implementation.
