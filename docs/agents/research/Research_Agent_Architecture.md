# Research Agent Architecture

**Version:** 0.1  
**Owner:** Project0  
**Last Updated:** 2026-08-20  

------------------------------------------------------------------------

## 1. Purpose

### Objective

Define the high-level architecture of the Research Agent and the major
functional components required to satisfy the Research Agent Functional
Specification.

### Scope

Describe the architectural organization of the Research Agent.
Implementation details, algorithms, and technology selections are
intentionally excluded.

------------------------------------------------------------------------

## 2. Architectural Principles

-   Modular component design.
-   Single responsibility for each component.
-   Deterministic components shall perform workflow, source access,
    metadata handling, artifact management, and validation tasks
    whenever AI reasoning is not required.
-   Research outputs shall be grounded in identifiable research sources.
-   Human judgment remains authoritative for research direction and
    conclusions.
-   Components communicate through well-defined typed interfaces.
-   Shared data models define information exchanged between components.
-   Platform components depend on interfaces rather than concrete
    implementations.
-   Research-specific behavior shall remain separate from reusable
    Project0 platform services.
-   Implementation technologies and external research sources may change
    without affecting the architecture.

------------------------------------------------------------------------

## 3. Architectural Workflow

The Research Agent extends the reusable Project0 platform with an
end-to-end research workflow. The Research Agent is accessed through the
reusable Dashboard Framework, which provides the browser interface while
remaining architecturally separate from the Research Agent services. The
Dashboard Framework hosts the Research Agent user interface within the
Dashboard Work Area and integrates research strategy generation,
external research source access, paper metadata retrieval, repository
knowledge, AI reasoning, research evaluation, validation, artifact
generation, and human review through the Platform Dispatcher.

The initial Research Agent implementation establishes a
human-in-the-loop research workflow. The workflow begins with a research
request, develops a research strategy, searches supported external
research sources, retrieves available paper metadata, evaluates and
ranks candidate papers, generates structured research artifacts,
preserves source and citation information, validates the generated
artifacts, and returns structured research results for human review.

The Dashboard Framework remains responsible for the shared application
shell, navigation, context, and Work Area hosting. Research Agent
components provide only agent-specific workflow behavior and interfaces.

``` mermaid
flowchart TD
    UI["Dashboard Framework"]
    A["Application Entry Point<br/><small>main.py</small>"]
    B["Platform Dispatcher"]
    C["Research Workflow"]

    D["Research Strategy Service"]
    Q["Research Query Service"]
    E["Research Source Service"]
    F["Paper Metadata Service"]
    G["Knowledge Service"]
    H["Research Evaluation Service"]
    I["Reasoning Service"]
    J["Research Artifact Service"]
    K["Validation Service"]

    L["Research Result"]

    UI --> A
    A --> B
    B --> C

    C --> D
    D --> Q
    Q --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
```

### Initial Runtime Flow

1.  `dashboard_app.py` creates the Dashboard application and configured
    Research Agent UI services.
2.  `main.py` creates the Platform Dispatcher.
3.  The Platform Dispatcher dispatches the requested Research Workflow.
4.  The Research Strategy Service analyzes the Research Request and
    produces a Research Strategy.
5.  The Research Source Service searches supported external research
    sources.
6.  The Paper Metadata Service retrieves and normalizes available paper
    metadata.
7.  The Knowledge Service retrieves relevant existing Project0 research
    context when applicable.
8.  The Research Evaluation Service evaluates and ranks candidate papers
    against the research question.
9.  The Reasoning Service performs AI-assisted research analysis where
    required.
10. The Research Artifact Service generates structured research
    artifacts.
11. Source and citation information is preserved with generated research
    artifacts.
12. The Validation Service validates required artifact structure and
    source information.
13. The Research Workflow returns a structured Research Result.
14. Research results are presented for human review through the
    Dashboard Framework.

------------------------------------------------------------------------

## 4. Architectural Components

### Platform Dispatcher

Provides the platform-level entry point for executing workflows.

Responsibilities:

-   Assemble the default platform services.
-   Dispatch platform workflows.
-   Create workflow tasks.
-   Submit tasks to the Workflow Engine.
-   Return structured workflow execution results.
-   Dispatch Research Workflows.
-   Assemble Research Workflow dependencies.
-   Provide workflow state access through platform interfaces.

### Workflow Engine

Coordinates synchronous workflow task execution.

Responsibilities:

-   Execute workflow tasks in sequence.
-   Maintain workflow and task identifiers.
-   Capture task outputs and failures.
-   Stop workflow execution after the first failed task.
-   Publish workflow and task events through an abstract interface.
-   Return structured workflow execution results.

### Knowledge Service

Coordinates deterministic repository knowledge retrieval.

Responsibilities:

-   Retrieve existing project research documentation.
-   Retrieve existing research artifacts when applicable.
-   Provide repository-grounded project context to research workflows.
-   Preserve parsing and selection warnings.
-   Return structured Knowledge Results.

### Shared Interfaces

Define stable contracts between platform and Research Agent components.

Initial Research Agent interfaces:

-   Research Workflow Interface
-   Research Strategy Interface
-   Research Query Interface
-   Research Source Interface
-   Paper Metadata Interface
-   Research Evaluation Interface
-   Research Artifact Interface

Interfaces allow components to depend on required capabilities rather
than concrete implementations.

### Shared Data Models

Define immutable data exchanged between Research Agent components.

Initial Research Agent model groups:

-   Research requests
-   Research results
-   Research strategies
-   Research source references
-   Paper references
-   Paper metadata
-   Research evaluations
-   Research artifacts

### Validation Service

Coordinates deterministic validation of Research Agent outputs.

Responsibilities:

-   Validate required research artifact structure.
-   Validate required source and citation information.
-   Aggregate validator results.
-   Preserve validator execution order.
-   Isolate validator execution failures.
-   Produce immutable Validation Results.

Research-specific validators may be added through the existing
Validation Interface.

### Reasoning Service

Provides AI reasoning through an abstract provider interface.

Responsibilities:

-   Analyze research questions.
-   Assist research strategy generation.
-   Analyze technical paper information.
-   Compare research methods and approaches.
-   Identify potential research gaps.
-   Generate experiment planning suggestions.
-   Generate structured research artifact content.

The Reasoning Service performs only tasks requiring AI-assisted
reasoning and does not directly access external research sources.

------------------------------------------------------------------------

### Research Strategy Service

Transforms a Research Request into a structured Research Strategy.

Responsibilities:

-   Analyze the research request.
-   Identify relevant research concepts and terminology.
-   Identify optional constraints and focus areas.
-   Generate search concepts for supported research sources.
-   Produce a structured Research Strategy.

------------------------------------------------------------------------

### Research Query Service

Transforms a structured Research Strategy into deterministic,
provider-ready research search queries.

Responsibilities:

- Convert research concepts into focused search queries.
- Generate multiple search perspectives for a research topic.
- Preserve deterministic query ordering.
- Remove duplicate query terms.
- Remain independent from external research source providers.
- Return structured query results for downstream Research Source Service
  execution.

The Research Query Service separates research intent definition from
external search execution. The Research Strategy Service determines what
should be researched, while the Research Query Service determines how
that research intent is expressed as searchable queries.

------------------------------------------------------------------------

------------------------------------------------------------------------

### Research Source Service

Provides controlled access to supported external research sources.

Responsibilities:

-   Execute research searches using a Research Strategy.
-   Query supported external research sources.
-   Normalize returned research source references.
-   Preserve source identifiers and locations.
-   Return structured source results and errors.

External source-specific behavior remains isolated behind typed
interfaces.

------------------------------------------------------------------------

### Paper Metadata Service

Retrieves and normalizes available metadata for candidate research
papers.

Responsibilities:

-   Retrieve available paper metadata.
-   Normalize title, authors, publication year, abstract, and source
    identifiers.
-   Preserve external source references.
-   Report missing metadata rather than inventing values.
-   Return structured metadata results and errors.

------------------------------------------------------------------------

### Research Evaluation Service

Evaluates candidate research papers against the Research Request and
Research Strategy.

Responsibilities:

-   Evaluate paper relevance.
-   Rank candidate papers.
-   Explain relevance to the research question.
-   Compare research methods and approaches.
-   Identify potential research gaps.
-   Support experiment planning analysis.
-   Preserve references to supporting research sources.

------------------------------------------------------------------------

### Research Artifact Service

Creates structured, reusable research artifacts.

Responsibilities:

-   Generate paper summary artifacts.
-   Generate literature comparison artifacts.
-   Generate research gap artifacts.
-   Generate experiment planning artifacts.
-   Preserve citation and source references.
-   Return structured Research Artifacts.

------------------------------------------------------------------------

### Research Workflow

Coordinates the complete Research Agent execution pipeline.

Responsibilities:

-   Coordinate Research Strategy, Research Source, Paper Metadata,
    Knowledge, Reasoning, Research Evaluation, Validation, and Research
    Artifact services.
-   Preserve internal workflow state.
-   Preserve source and citation information.
-   Produce immutable Research Results.
-   Support human review of research outputs.

------------------------------------------------------------------------

------------------------------------------------------------------------

## Research Source Provider Architecture

The Research Agent uses a provider-based architecture to isolate
external research source implementations from Research Agent workflow
execution.

The Research Source Service communicates through a typed Research Source
Provider interface rather than directly depending on a specific external
research source implementation.

Supported research source providers include:

-   Semantic Scholar Source Provider
    -   Provides production research source access through Semantic
        Scholar.
    -   Retrieves identifiable research references from an external
        research source.
-   Stub Research Source Provider
    -   Provides deterministic research source behavior for testing,
        demonstrations, and acceptance validation.
    -   Allows workflow validation without requiring external research
        source availability.

The provider abstraction preserves the existing workflow architecture
while allowing research sources to be replaced or extended without
changing Research Agent workflow components.

Initial provider architecture:

``` text
Research Workflow
        |
        v
Research Source Service
        |
        v
Research Source Provider Interface
        |
        +------------------------------+
        |                              |
        v                              v
Semantic Scholar Provider        Stub Provider
(production source)              (deterministic validation)
```

The provider abstraction supports the Project0 architectural principle
that platform components depend on interfaces rather than concrete
implementations.

------------------------------------------------------------------------

## 5. External Dependencies

The Research Agent interacts with:

-   Supported external research sources
-   Technical paper metadata
-   Project0 repository knowledge
-   Existing research artifacts
-   Python runtime environment
-   pytest test framework
-   Validation tools
-   AI reasoning provider
-   Dashboard Framework (FastAPI, Jinja2 templates, shared dashboard
    resources)

------------------------------------------------------------------------

## 6. Design Constraints

-   Research outputs shall preserve identifiable source and citation
    information.
-   Source information shall remain distinguishable from AI-generated
    analysis.
-   Missing source or metadata information shall not be invented.
-   Platform components shall communicate through typed interfaces.
-   Shared data models shall define information exchanged between
    components.
-   Platform components shall depend on interfaces rather than concrete
    implementations where practical.
-   External research source access shall occur through defined service
    interfaces.
-   Research-specific behavior shall remain separate from reusable
    Project0 platform services.
-   Research evaluation does not independently establish scientific
    correctness.
-   Human research judgment remains authoritative.
-   The Dashboard Framework shall remain a reusable platform interface
    and shall not contain Research Agent business logic.
-   Agent user interfaces shall render within Dashboard Work Areas
    rather than operating as independent applications.
-   Initial implementation shall avoid semantic retrieval, vector-based
    knowledge search, and multi-agent research workflows unless later
    requirements demonstrate the need.

------------------------------------------------------------------------

## 7. Future Architectural Expansion

Future versions may introduce:

-   Semantic research retrieval
-   Embedding generation
-   Vector-based knowledge search
-   Additional external research sources
-   Expanded research artifact types
-   Improved research evaluation services
-   Multi-agent research workflows
-   Scheduled research monitoring
-   Additional AI providers
-   Additional validation services
-   Asynchronous workflow execution
