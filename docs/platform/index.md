# Platform Documentation

The Project0 platform documentation describes the shared services, interface framework, communication boundaries, common data contracts, validation status, and reusable capabilities that support Project0 agents.

This documentation set focuses on platform-level behavior shared across agents rather than on agent-specific workflow implementation.

## Documentation Set

| Document | Purpose |
|---|---|
| [Dashboard Design](Dashboard_Design.md) | Describes the shared Dashboard Framework, layout, status presentation, workspace structure, and agent integration points. |
| [Component Communication Design](Component_Communication_Design.md) | Documents runtime composition, service interactions, workflow boundaries, events, and failure propagation. |
| [Shared Data Models and Error Contracts](Shared_Data_Models_and_Error_Contracts.md) | Defines shared model families, status values, repository errors, and boundary-specific failure behavior. |
| [Agent Skills Design](Agent_Skills_Design.md) | Describes repository-local Agent Skill format, discovery, validation, loading, and reasoning integration. |
| [Project0 Validation Status](Project0_Validation_Status.md) | Records project-level verification and validation status tied to the implemented repository state. |

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

For project goals, development practices, roadmap, and implementation status, see the [Project Documentation](../project/index.md).

For agent-specific behavior, see:

- [Documentation Agent Documentation](../agents/documentation/index.md)
- [Research Agent Documentation](../agents/research/index.md)

For the complete documentation portal, return to the [Project0 Documentation Home](../index.md).

## Source of Truth

The Project0 source repository is the implementation source of truth. Platform documentation should remain synchronized with the implemented shared services, interfaces, contracts, Dashboard behavior, validation logic, and reusable platform capabilities, and should avoid claims not supported by the implementation.
