# Project0 Platform Documentation

The Project0 Platform documentation describes the goals, structure, development practices, implementation roadmap, current status, shared services, interface framework, communication boundaries, common data contracts, validation status, and reusable capabilities of the Project0 platform.

This documentation set provides the project-level context and platform-level design needed to understand how Project0 is organized, developed, validated, maintained, and used to support specialized agents.

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
| [Dashboard Design](Dashboard_Design.md) | Describes the shared Dashboard Framework, layout, status presentation, workspace structure, and agent integration points. |
| [Component Communication Design](Component_Communication_Design.md) | Documents runtime composition, service interactions, workflow boundaries, events, and failure propagation. |
| [Shared Data Models and Error Contracts](Shared_Data_Models_and_Error_Contracts.md) | Defines shared model families, status values, repository errors, and boundary-specific failure behavior. |
| [Agent Skills Design](Agent_Skills_Design.md) | Describes repository-local Agent Skill format, discovery, validation, loading, and reasoning integration. |
| [Project0 Validation Status](Project0_Validation_Status.md) | Records project-level verification and validation status tied to the implemented repository state. |

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

## Platform Responsibilities

The shared Project0 platform provides infrastructure used by specialized agents, including:

- configuration and common services;
- repository and context access;
- shared models and contracts;
- workflow coordination;
- reasoning-provider integration;
- validation services;
- Dashboard composition and shared interface behavior;
- reusable Agent Skill support.

Agent-specific workflow semantics remain documented within each agent's own documentation set.

## Platform Boundaries

Platform documentation should describe only behavior that is shared, reusable, or infrastructural across Project0.

Behavior unique to an individual agent belongs in that agent's documentation, including workflow stages, request contracts, result models, interface details, and agent-specific validation.

## Related Documentation

For agent-specific behavior, interfaces, workflows, and validation, see:

- [Documentation Agent Documentation](../documentation-agent/index.md)
- [Research Agent Documentation](../research-agent/index.md)

For the complete documentation portal, return to the [Project0 Documentation Home](../index.md).

## Source of Truth

The Project0 source repository is the implementation source of truth. Project0 Platform documentation should remain synchronized with the implemented repository structure, configuration, tests, shared services, interfaces, contracts, Dashboard behavior, validation logic, and reusable platform capabilities, and should avoid claims not supported by the implementation.
