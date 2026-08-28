# Research Agent Design

**Version:** 0.3  
**Owner:** Project0  
**Last Updated:** 2026-08-28

---

## 1. Purpose

### Objective

Define the internal design of the major Research Agent components
required to implement the Research Agent Functional Specification.

### Scope

Describe the purpose, responsibilities, interfaces, inputs, outputs,
dependencies, and future considerations for Research Agent components.
Architectural implementation boundaries and service abstractions are
included where required to define component responsibilities.

---

## 2. Component Design Principles

-   Each component has a single responsibility.
-   Components communicate through well-defined typed interfaces.
-   Shared immutable data models define information exchanged between
    components.
-   Components depend on interfaces rather than concrete implementations
    where practical.
-   Deterministic processing shall be used whenever AI reasoning is not
    required.
-   Components shall be independently testable.
-   Minimize coupling between components.
-   Maximize reuse across future AI agents.
-   Research outputs shall preserve identifiable source and citation
    information.
-   Research-specific behavior shall remain separate from reusable
    Project0 platform services.

---

## 3. Component Overview

The Research Agent reuses the existing Project0 platform foundation and
adds research-specific components required to transform research
questions into structured, evidence-grounded research artifacts. The
Research Agent is hosted within the reusable Dashboard Framework, which
provides the browser interface while remaining architecturally separate
from the agent services.

Existing Project0 platform components reused by the Research Agent
include:

-   Dashboard Framework
-   Platform Dispatcher
-   Workflow Engine
-   Knowledge Service
-   Reasoning Service
-   Validation Service
-   Artifact Services
-   Shared Interfaces
-   Shared Data Models

Initial Research Agent-specific components include:

-   Research Workflow
-   Research Strategy Service
-   Research Query Service
-   Research Source Service
-   Research Source Provider Interface
-   Paper Metadata Service
-   Research Evaluation Service
-   Context Document Ingestion
-   Existing Research Context Analysis
-   Per-Paper Analysis
-   Research Direction Analysis
-   Research Artifact Service

The Platform Dispatcher provides the platform-level entry point. It
creates workflow tasks and submits them to the Workflow Engine. The
Research Workflow coordinates the research-specific services and
existing Project0 platform services required to produce structured
research results.

---

## 4. Component Specifications

### 4.1 Platform Dispatcher

#### Purpose

Provide the platform-level entry point for assembling services and
dispatching Research Agent workflows.

#### Responsibilities

-   Assemble the Research Workflow.
-   Create research workflow tasks.
-   Dispatch Research Workflows.
-   Return structured research workflow results.
-   Preserve separation between platform routing and Research Agent
    behavior.

#### Interfaces

##### Provides

-   Run research workflow.

##### Consumes

-   Workflow Interface.
-   Research Workflow Interface.
-   Research workflow models.

#### Design Notes

-   Coordinates platform services without implementing research behavior
    directly.
-   Uses existing Project0 platform dispatch patterns.
-   Provides a common entry point for the Documentation Agent, Research
    Agent, and future agents.

#### Inputs

-   Research workflow request

#### Outputs

-   Research workflow result

#### Required Services

-   Workflow Interface
-   Research Workflow Interface

#### Future Considerations

-   Additional agent routing
-   Multi-agent workflow coordination

---

### 4.2 Dashboard Framework

#### Purpose

Provide the reusable browser-based user interface for Project0 services
and AI agents.

#### Responsibilities

-   Host Research Agent pages within the shared framework.
-   Provide shared navigation, context, and Work Area hosting.
-   Provide the Dashboard Work Area for Research Agent interaction.
-   Remain independent of Research Agent business logic.

#### Design Notes

-   Reuses the existing Dashboard Framework.
-   Research Agent-specific pages render within the Dashboard Work Area.
-   Research Agent UI behavior remains separate from shared Dashboard
    Framework behavior.

---

### 4.3 Workflow Engine

#### Purpose

Execute Project0 workflow tasks and return structured execution results.

#### Responsibilities

-   Execute Research Agent workflow tasks.
-   Preserve workflow identifiers.
-   Capture task outputs.
-   Convert task exceptions into failed task results.
-   Return structured workflow execution results.

#### Design Notes

-   Reuses the existing Project0 Workflow Engine.
-   Does not implement research-specific behavior.
-   Research workflow coordination remains the responsibility of the
    Research Workflow.

---

### 4.4 Knowledge Service

#### Purpose

Provide Project0 repository knowledge relevant to Research Agent
requests.

#### Responsibilities

-   Retrieve existing project research documentation.
-   Retrieve existing research artifacts when applicable.
-   Provide repository-grounded project context to research workflows.

#### Design Notes

-   Reuses the existing deterministic Knowledge Service.
-   Does not perform external literature discovery.
-   External research sources remain separate from repository knowledge
    retrieval.

#### Future Considerations

-   Semantic retrieval
-   Embedding generation
-   Vector search

---

### 4.5 Reasoning Service

#### Purpose

Perform AI-assisted research reasoning.

#### Responsibilities

-   Analyze research questions.
-   Assist research strategy generation.
-   Analyze technical paper information.
-   Analyze Existing Research Context document content.
-   Perform structured per-paper interpretation.
-   Compare research methods and approaches.
-   Perform cross-paper synthesis for Research Direction Analysis.
-   Identify potential research gaps.
-   Generate experiment planning suggestions.
-   Generate structured research artifact content.

#### Interfaces

##### Provides

-   Analyze research request.
-   Evaluate research information.
-   Generate research analysis.

##### Consumes

-   Research question.
-   Research source information.
-   Paper metadata.
-   Optional Existing Research Context.
-   Project knowledge.

#### Design Notes

-   Performs only tasks requiring AI-assisted reasoning.
-   Does not directly access external research sources.
-   Does not independently establish scientific validity.
-   Distinguishes source information from generated analysis.

#### Required Services

-   AI Reasoning Provider

#### Future Considerations

-   Multiple reasoning providers
-   Model routing
-   Context-size management

---

### 4.6 Validation Service

#### Purpose

Coordinate validation of Research Agent workflow outputs.

#### Responsibilities

-   Validate required research artifact structure.
-   Validate required source and citation information.
-   Validate referenced context items and paper identifiers.
-   Validate candidate research direction context motivation and
    literature evidence unless explicitly marked speculative.
-   Reject unknown source identifiers.
-   Aggregate validation results.
-   Preserve structured validation warnings and errors.

#### Design Notes

-   Reuses the existing Project0 Validation Service where practical.
-   Research-specific validators may be added through existing
    validation interfaces.
-   Validation does not determine scientific correctness.

#### Future Considerations

-   Citation validator
-   Research artifact validator
-   Metadata consistency validator

---

### 4.7 Shared Interfaces

#### Purpose

Define stable public contracts between Project0 and Research Agent
components.

#### Initial Research Interfaces

-   Research Workflow Interface
-   Research Strategy Interface
-   Research Source Interface
-   Paper Metadata Interface
-   Research Evaluation Interface
-   Existing Research Context Analysis Interface
-   Per-Paper Analysis Interface
-   Research Direction Analysis Interface
-   Research Artifact Interface

#### Design Notes

-   Interfaces use Python structural protocols.
-   Components depend on required capabilities rather than specific
    implementations.
-   Research-specific interfaces shall remain separate from generic
    platform interfaces.
-   Interfaces shall remain small and aligned with implemented component
    capabilities.

---

### 4.8 Shared Data Models

#### Purpose

Define immutable information exchanged between Research Agent
components.

#### Initial Research Models

-   Research Request
-   Research Result
-   Research Strategy
-   Research Source Reference
-   Paper Reference
-   Paper Metadata
-   Research Evaluation
-   Existing Research Context
-   Paper Analysis
-   Research Direction Analysis
-   Research Artifact

#### Design Notes

-   Models use immutable dataclasses where practical.
-   Result models preserve structured outputs, warnings, and errors.
-   Source and citation information shall remain associated with
    research outputs.
-   Shared models prevent component-specific communication formats.

---

### 4.9 Context Document Ingestion

#### Purpose

Provide controlled ingestion and text extraction for an optional
Existing Research Context document.

#### Responsibilities

-   Accept a context document through a simple file-selection/upload
    interaction.
-   Support text-based PDF, Markdown, and plain-text documents.
-   Extract source content without storing a copy of the source document.
-   Preserve page- or section-level provenance.
-   Process large documents using bounded chunking with implementation
    limits to be defined.
-   Clearly report extraction failures.
-   Reject image-only or scanned PDF documents requiring OCR.

#### Design Notes

-   File handling and text extraction remain separate from research
    reasoning.
-   OCR support is deferred to a future enhancement.
-   A selected context document that cannot be extracted shall not
    silently revert to the no-context workflow.

#### Inputs

-   Optional Existing Research Context document

#### Outputs

-   Extracted context document content
-   Source provenance
-   Extraction warnings or errors

---

### 4.10 Existing Research Context Analysis

#### Purpose

Transform extracted context document content into structured Existing
Research Context.

#### Responsibilities

-   Identify the research problem.
-   Identify prior work.
-   Identify implemented approaches.
-   Identify findings and limitations.
-   Identify unresolved questions.
-   Identify stated future work.
-   Preserve source references for extracted context findings.

#### Interfaces

##### Provides

-   Analyze Existing Research Context.

##### Consumes

-   Extracted context document content.
-   Reasoning Service.

#### Design Notes

-   Context findings are source-derived.
-   Source-derived context findings remain distinguishable from generated
    analysis.
-   Context provenance is preserved at page- or section-level.
-   Context analysis failures are clearly reported.

#### Inputs

-   Extracted context document content
-   Source provenance

#### Outputs

-   Existing Research Context

#### Required Services

-   Reasoning Service

---

### 4.11 Per-Paper Analysis

#### Purpose

Produce structured technical analysis for each retained paper.

#### Responsibilities

-   Identify the paper problem and approach.
-   Identify representations and modalities.
-   Identify the learning or alignment objective.
-   Identify datasets or tasks.
-   Identify findings and limitations.
-   Explain relevance to the current research.
-   Preserve evidence references.

#### Interfaces

##### Provides

-   Analyze retained paper.

##### Consumes

-   Research Request.
-   Research Strategy.
-   Paper Metadata.
-   Research Evaluation.
-   Reasoning Service.

#### Design Notes

-   Per-paper analysis is source-derived interpretation.
-   Missing source information shall not be invented.
-   Evidence references remain associated with analysis findings.

#### Inputs

-   Research Request
-   Research Strategy
-   Paper Metadata
-   Research Evaluation

#### Outputs

-   Paper Analysis

#### Required Services

-   Reasoning Service

---

### 4.12 Research Direction Analysis

#### Purpose

Analyze retained paper analyses together with optional Existing Research
Context to identify evidence-grounded research directions.

#### Responsibilities

-   Perform cross-paper comparison.
-   Produce structured synthesis findings including themes, comparisons,
    shared limitations, and unresolved questions.
-   Identify candidate research directions.
-   Ground candidate directions in context motivation and literature
    evidence unless explicitly marked speculative.
-   Preserve provenance for supporting context and paper evidence.

#### Interfaces

##### Provides

-   Analyze research directions.

##### Consumes

-   Research Request.
-   Research Strategy.
-   Optional Existing Research Context.
-   Paper Analyses.
-   Reasoning Service.

#### Design Notes

-   Cross-paper synthesis is functionality within Research Direction
    Analysis rather than a separate service.
-   Research directions are Research Agent inference grounded in
    source-derived context and per-paper interpretation.
-   The detailed Research Direction Analysis output contract remains to
    be defined.

#### Inputs

-   Research Request
-   Research Strategy
-   Optional Existing Research Context
-   Paper Analyses

#### Outputs

-   Synthesis findings
-   Candidate research directions

#### Required Services

-   Reasoning Service

---

### 4.13 Research Strategy Service

#### Purpose

Transform a research question into a structured research strategy.

#### Responsibilities

-   Analyze the research request.
-   Incorporate optional Existing Research Context when provided.
-   Support open-ended research requests when Existing Research Context
    is available.
-   Identify the research objective and relevant research concepts.
-   Identify explicit research sub-questions when present.
-   Identify optional constraints and focus areas.
-   Produce a structured Research Strategy.

#### Interfaces

##### Provides

-   Generate research strategy.

##### Consumes

-   Research Request.
-   Optional Existing Research Context.
-   Reasoning Service.

#### Design Notes

-   Research strategy generation may use AI reasoning.
-   The service does not execute external research searches.
-   Search-term generation remains the responsibility of the Research
    Query Service.
-   Search execution remains the responsibility of the Research Source
    Service.

#### Inputs

-   Research Request

#### Outputs

-   Research Strategy

#### Required Services

-   Reasoning Service

#### Future Considerations

-   Strategy refinement
-   Search history awareness
-   User-defined strategy templates

---

### 4.10 Research Query Service

#### Purpose

Transform a structured Research Strategy into deterministic,
provider-ready research search terms.

#### Responsibilities

-   Convert research concepts into focused search terms.
-   Preserve deterministic query ordering.
-   Remove duplicate query terms.
-   Return an enriched Research Strategy containing provider-ready
    search terms.

#### Design Notes

-   The service remains independent from external research source
    providers.
-   The Research Strategy Service determines what should be researched.
-   The Research Query Service determines how that research intent is
    expressed as searchable terms.

#### Inputs

-   Research Strategy

#### Outputs

-   Research Strategy

---

### 4.14 Research Source Service

#### Purpose

Provide controlled access to supported external research sources.

#### Responsibilities

-   Execute research searches using a Research Strategy.
-   Query configured external research source providers.
-   Combine results from multiple configured research source providers.
-   Normalize returned research source references.
-   Preserve source identifiers and locations.
-   Return structured source results and errors.

#### Interfaces

##### Provides

-   Search research sources.
-   Retrieve research source information.

##### Consumes

-   Research Strategy.
-   External research source adapters.

#### Design Notes

-   External source access is isolated behind a typed interface.
-   Multiple configured providers may contribute source references to a
    single research workflow.
-   The service does not perform research relevance evaluation.
-   Source-specific behavior shall remain isolated from the Research
    Workflow.
-   Initial implementation should support the minimum number of external
    sources required to provide useful research output.

#### Inputs

-   Research Strategy

#### Outputs

-   Research Source References

#### External Dependencies

-   Supported external research sources

#### Future Considerations

-   Additional research sources
-   Source-specific adapters
-   Search result caching
-   Rate-limit handling

---

### 4.15 Paper Metadata Service

#### Purpose

Retrieve and normalize available metadata for candidate research papers.

#### Responsibilities

-   Retrieve available paper metadata.
-   Normalize title, author, publication year, abstract, and source
    identifiers.
-   Preserve external source references.
-   Return structured metadata results and errors.

#### Interfaces

##### Provides

-   Retrieve paper metadata.

##### Consumes

-   Research Source References.
-   External research source adapters.

#### Design Notes

-   Performs deterministic metadata normalization where practical.
-   Does not evaluate paper relevance.
-   Missing metadata shall be reported rather than invented.

#### Inputs

-   Research Source References

#### Outputs

-   Paper Metadata

#### Future Considerations

-   DOI enrichment
-   Citation metadata
-   Publication venue normalization

---

### 4.16 Research Evaluation Service

#### Purpose

Evaluate candidate research papers against the research question and
research strategy.

#### Responsibilities

-   Evaluate paper relevance using a bounded relevance scale.
-   Distinguish direct research-question alignment from partial,
    adjacent, or topical relevance.
-   Apply consistent relevance criteria across evaluated papers.
-   Explain relevance to the research question.

#### Interfaces

##### Provides

-   Evaluate candidate paper.
-   Rank candidate papers.

##### Consumes

-   Research Request.
-   Research Strategy.
-   Paper Metadata.
-   Reasoning Service.

#### Design Notes

-   Uses AI reasoning where semantic evaluation is required.
-   Relevance evaluation shall preserve the distinction between source
    facts and generated analysis.
-   Evaluation results shall preserve references to supporting papers.
-   Valid provider relevance scores are normalized for downstream use.
-   Candidate papers are evaluated in bounded batches and validated
    batch results are combined into the complete evaluation result.
-   Evaluation provider responses within a batch that violate required
    source traceability or coverage constraints may be retried once
    before the evaluation is reported as failed.
-   Human research judgment remains authoritative.

#### Inputs

-   Research Request
-   Research Strategy
-   Paper Metadata

#### Outputs

-   Research Evaluations

#### Required Services

-   Reasoning Service

#### Future Considerations

-   Improved evaluation scoring
-   Configurable ranking criteria
-   Cross-paper evidence analysis

---

### 4.17 Research Artifact Service

#### Purpose

Create structured, reusable research artifacts from validated Research
Agent outputs.

#### Responsibilities

-   Generate paper summary artifacts.
-   Generate literature comparison artifacts.
-   Generate research gap artifacts.
-   Generate experiment planning artifacts.
-   Generate saved research packages containing the request, context
    summary, research strategy, retained papers, per-paper analyses,
    synthesis findings, candidate directions, provenance, and validation
    status.
-   Preserve citation and source references.
-   Return structured Research Artifacts.

#### Interfaces

##### Provides

-   Generate research artifact.

##### Consumes

-   Research Evaluations.
-   Paper Metadata.
-   Research Request.
-   Optional Existing Research Context.
-   Paper Analyses.
-   Research Direction Analysis.

#### Design Notes

-   Research artifacts preserve source provenance.
-   Artifact generation shall not modify repository documentation
    directly.
-   Repository preservation of approved research artifacts may be
    coordinated with the Documentation Agent or existing artifact
    services.

#### Inputs

-   Research Evaluations
-   Paper Metadata
-   Research Request
-   Optional Existing Research Context
-   Paper Analyses
-   Research Direction Analysis

#### Outputs

-   Research Artifacts

#### Future Considerations

-   Expanded research artifact types
-   Artifact persistence policies
-   Cross-project research artifacts

---

### 4.18 Research Workflow

#### Purpose

Coordinate the complete Research Agent execution pipeline.

#### Responsibilities

-   Coordinate Research Strategy, Research Query, Research Source, Paper
    Metadata, Knowledge, Reasoning, Research Evaluation, Validation, and
    Research Artifact services.
-   Preserve internal workflow state.
-   Preserve existing workflow semantics when no Existing Research
    Context document is provided.
-   Coordinate context ingestion and analysis when an Existing Research
    Context document is provided.
-   Clearly report requested context extraction or analysis failures
    without silently reverting to the no-context workflow.
-   Rank evaluated papers by relevance and retain the configured maximum
    number of results.
-   Preserve all discovered source references for traceability.
-   Generate per-paper analyses from retained evaluations.
-   Coordinate Research Direction Analysis across retained paper
    analyses and optional Existing Research Context.
-   Generate research artifacts from retained evaluations and analyses.
-   Produce immutable Research Results.
-   Preserve source and citation information.
-   Support human review of research outputs.

#### Design Notes

-   Research Workflow execution is initiated through the Platform
    Dispatcher.
-   Research Agent UI interactions are hosted by the Dashboard
    Framework.
-   External source access occurs only through the Research Source
    Service.
-   AI reasoning does not directly access external research sources.
-   Research artifacts remain reviewable outputs rather than
    authoritative research conclusions.

---

### Research Source Provider Design

#### Purpose

Define the provider-based design used to isolate external research
source implementations from Research Agent workflow components.

#### Design Notes

The Research Source Service communicates through a typed provider
interface rather than depending directly on a specific external research
source implementation.

Research source providers are responsible for retrieving research source
references while preserving source identifiers and locations.

Initial provider implementations include:

-   Semantic Scholar Source Provider
    -   Provides production research source access.
    -   Retrieves identifiable research references from Semantic
        Scholar.
-   arXiv Source Provider
    -   Provides research source access through the arXiv API.
    -   Retrieves identifiable academic paper references from arXiv.
-   Crossref Source Provider
    -   Provides research source access through the Crossref API.
    -   Retrieves identifiable research references from Crossref.
-   OpenAlex Source Provider
    -   Provides research source access through the OpenAlex API.
    -   Retrieves identifiable research references from OpenAlex.
-   OpenReview Source Provider
    -   Provides research source access through the OpenReview API.
    -   Retrieves identifiable research references from OpenReview.
-   Stub Research Source Provider
    -   Provides deterministic research source behavior.
    -   Supports automated testing, demonstrations, and acceptance
        validation without requiring external research source
        availability.

The provider abstraction allows Research Agent workflows to remain
unchanged when external research sources are added, replaced, configured
together, or tested through deterministic implementations.

Initial provider interaction:

``` text
Research Workflow
        |
        v
Research Source Service
        |
        v
Research Source Provider Interface
        |
        +---------------------------------------------------------------+
        |              |              |              |              |
        v              v              v              v              v
Semantic Scholar  arXiv Provider  Crossref       OpenAlex       OpenReview
Provider          (external       Provider       Provider       Provider
(production       source)         (external      (external      (external
source)                           source)        source)        source)
        |
        v
Stub Provider
(deterministic validation)
```

The provider design follows the Project0 principle that components
depend on interfaces rather than concrete implementations.

---

### Revision Workflow Support

The Research Workflow supports a revision path when a user requests
changes to a generated research request or research output.

#### Responsibilities

-   Preserve the original research request.
-   Preserve optional research constraints.
-   Accept appended or modified revision instructions.
-   Resume normal research processing after resubmission.
-   Preserve source and citation information during revision.

#### Design Notes

-   Revision creates a new research reasoning cycle.
-   Existing source evidence should remain available when applicable.
-   Revised research direction may trigger additional source discovery.

---

## 5. Interface Design Principles

-   Interfaces shall remain technology independent.
-   Components communicate only through public typed interfaces.
-   Components shall not directly access another component's internal
    state.
-   Components shall depend on interfaces rather than concrete
    implementations where practical.
-   Interface contracts shall remain backward compatible whenever
    practical.
-   Shared data models shall define information exchanged between
    components.
-   Concrete implementations may satisfy interfaces through structural
    typing.
-   Interfaces shall remain small and aligned with implemented component
    capabilities.
-   External research source implementations shall remain isolated
    behind Research Source interfaces.

---

## 7. Component Interactions

The Platform Dispatcher provides the platform-level entry point and
submits Research Agent workflow tasks to the Workflow Engine.

The initial Research Workflow follows this sequence:

1.  The user submits a Research Request through the Dashboard Framework.
2.  The Platform Dispatcher creates and dispatches the Research
    Workflow.
3.  When provided, the selected Existing Research Context document is
    ingested and analyzed.
4.  The Research Strategy Service analyzes the Research Request and
    optional Existing Research Context.
5.  The Reasoning Service assists with research concept and strategy
    generation when required.
6.  The Research Strategy Service returns a Research Strategy.
6.  The Research Query Service enriches the Research Strategy with
    deterministic provider-ready search terms.
8.  The Research Source Service searches configured external research
    source providers.
9.  External source results from configured providers are combined and
    normalized into Research Source References.
10.  The Paper Metadata Service retrieves and normalizes available
    metadata.
11. The Knowledge Service retrieves relevant existing Project0 research
    context when applicable.
12. The Research Evaluation Service evaluates candidate papers against
    the Research Request and Research Strategy.
13. The Reasoning Service performs semantic research evaluation where
    required.
14. Candidate papers are ranked by relevance and the configured maximum
    number of results is retained.
15. Per-Paper Analysis produces structured technical analysis for each
    retained paper.
16. Research Direction Analysis performs cross-paper comparison and
    identifies candidate research directions.
17. The Research Artifact Service generates structured research
    artifacts from retained evaluations and analyses.
18. Citation and source references are preserved with the generated
    artifacts.
19. The Validation Service validates required artifact structure and
    source information.
20. The Research Workflow returns a structured Research Result.
21. Research results are presented for human review through the
    Dashboard Framework.

The Dashboard Framework remains responsible for the shared application
shell, including navigation, context, and Work Area hosting. The
Research Agent provides only agent-specific workflow interactions within
the Dashboard Work Area.

Research Agent-specific behavior remains isolated from reusable Project0
platform services. External research source behavior remains isolated
behind the Research Source Service and its interfaces.

---

## 7. Design Constraints

-   Preserve modularity.
-   Use deterministic processing whenever AI reasoning is not required.
-   Maintain vendor neutrality.
-   Support future extensibility.
-   Use typed interfaces between platform and Research Agent components.
-   Use shared immutable models for component communication.
-   Depend on interfaces rather than concrete implementations where
    practical.
-   Preserve source and citation information throughout the research
    workflow.
-   External research source access shall occur through defined service
    interfaces.
-   Missing source or metadata information shall not be invented.
-   Existing Research Context source documents shall not be copied into
    Project0 storage by the Research Agent.
-   Existing Research Context provenance shall be preserved at page- or
    section-level.
-   Image-only or scanned PDF context documents requiring OCR are outside
    the current implementation scope.
-   AI-generated analysis shall remain distinguishable from source
    information.
-   Source-derived context findings, source-derived per-paper
    interpretation, and Research Agent inference shall remain
    distinguishable.
-   Research evaluation does not independently establish scientific
    correctness.
-   Human research judgment remains authoritative.
-   Initial implementation shall avoid semantic retrieval, vector
    search, and multi-agent research workflows unless later requirements
    demonstrate the need.
