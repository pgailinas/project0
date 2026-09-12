# Project Documentation

The Project0 project documentation describes the goals, structure, development practices, implementation roadmap, and current status of the Project0 platform.

This documentation set provides the project-level context needed to understand how Project0 is organized, developed, validated, and maintained.

## Documentation Set

| Document | Purpose |
|---|---|
| [Project Charter](Project_Charter.md) | Defines the Project0 vision, goals, scope, stakeholders, principles, and intended outcomes. |
| [Project Directory Structure](Project_Directory_Structure.md) | Describes repository organization and the responsibilities of major directories and file groups. |
| [Development Environment](Development_Environment.md) | Documents installation, runtime configuration, development tools, startup procedures, and environment requirements. |
| [Development Standards](Development_Standards.md) | Defines engineering, implementation, validation, review, and AI-assisted development standards. |
| [Documentation Standards](Documentation_Standards.md) | Defines documentation ownership, structure, source-grounding, maintenance, and publishing conventions. |
| [Testing Guide](Testing_Guide.md) | Provides project-wide guidance for running, interpreting, and maintaining the Project0 test suite. |
| [Implementation Roadmap](Implementation_Roadmap.md) | Describes planned phases, deliverables, priorities, and future implementation direction. |
| [Implementation Status](Implementation_Status.md) | Records the current implementation state, completed work, active capabilities, gaps, and known boundaries. |

## Project Scope

Project0 is an AI-native software development platform designed to support specialized AI agents, shared platform services, controlled workflows, validation, and documentation-first development practices.

Project-level documentation focuses on concerns that apply across the repository rather than on the internal behavior of any one agent.

## Development Principles

Project0 development emphasizes:

- documentation as a first-class, version-controlled project artifact;
- source code, tests, and configuration as authority for implemented behavior;
- deterministic processing where model reasoning is unnecessary;
- clear separation between shared platform responsibilities and agent-specific behavior;
- bounded, reviewable AI-assisted workflows;
- validation before changes are treated as complete;
- small, coherent changes with corresponding test and documentation updates.

## Related Documentation

For shared platform architecture and service-level design, see the [Platform Documentation](../platform/index.md).

For agent-specific behavior, interfaces, workflows, and validation, see:

- [Documentation Agent Documentation](../agents/documentation/index.md)
- [Research Agent Documentation](../agents/research/index.md)

For the complete documentation portal, return to the [Project0 Documentation Home](../index.md).

## Source of Truth

The Project0 source repository is the implementation source of truth. Project documentation should remain synchronized with the implemented repository structure, configuration, tests, and verified project status, and should avoid claims not supported by the implementation.
