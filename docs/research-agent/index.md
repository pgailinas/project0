# Research Agent Documentation

The Project0 Research Agent supports structured literature discovery, relevance evaluation, paper analysis, and research-direction synthesis for a user-defined research question.

This documentation set describes the Research Agent from requirements and architecture through interface behavior, workflow execution, testing, and validation.

## Documentation Set

| Document | Purpose |
|---|---|
| [Research Agent Charter](Research_Agent_Charter.md) | Defines the Research Agent mission, scope, responsibilities, and boundaries. |
| [Research Agent Functional Specification](Research_Agent_Functional_Spec.md) | Describes functional requirements, expected behaviors, inputs, outputs, and workflow capabilities. |
| [Research Agent Architecture](Research_Agent_Architecture.md) | Documents major components, service boundaries, data flow, and architectural relationships. |
| [Research Agent Design](Research_Agent_Design.md) | Describes the detailed software design and implementation structure of the Research Agent. |
| [Research Agent Interface Design](Research_Agent_Interface_Design.md) | Documents the Research Agent web interface, controls, workflow presentation, and user interaction model. |
| [Research Agent Testing Guide](Research_Agent_Testing_Guide.md) | Provides guidance for running and interpreting Research Agent tests. |
| [Research Agent Test Plan](Research_Agent_Test_Plan.md) | Defines intended test coverage, validation approach, and acceptance criteria. |
| [Research Agent Test Results](Research_Agent_Test_Results.md) | Records Research Agent validation and test results. |

## Research Workflow

The Research Agent executes a staged workflow:

1. **Request** — Accept the research question, optional existing research context, research guidance, and result limit.
2. **Strategy** — Build a bounded research strategy and complementary search queries.
3. **Source Search** — Search configured research providers for candidate papers.
4. **Metadata** — Retrieve and normalize paper metadata.
5. **Evaluation** — Evaluate candidate papers for relevance and perform structured analysis where applicable.
6. **Artifacts** — Build research results and supporting synthesis artifacts.
7. **Complete** — Present the completed research output, warnings, and workflow summary.

The Research Agent interface reports live workflow progress so the displayed stage reflects the active backend operation.

## Major Capabilities

The Research Agent supports:

- multi-source literature discovery;
- bounded multi-query retrieval;
- configurable research-source providers;
- relevance scoring and ranking;
- structured paper analysis;
- analysis of existing research context supplied by the user;
- research-direction synthesis;
- downloadable Markdown research results;
- live workflow-stage reporting;
- runtime System Status information.

Provider selection and reasoning-model configuration are controlled by Project0 configuration and may vary by deployment.

## Related Documentation

For project goals, development practices, roadmap, and implementation status, shared platform architecture, services, contracts, Dashboard behavior, and validation, see the [Platform Documentation](../platform/index.md).

For the complete documentation portal, return to the [Project0 Documentation Home](../index.md).

## Source of Truth

The Project0 source repository is the implementation source of truth. Documentation should be updated when Research Agent behavior, workflow stages, configuration, interfaces, or validation coverage change.
