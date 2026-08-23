# Research Agent Interface Design

**Version:** 0.1  
**Owner:** Project0  
**Last Updated:** 2026-08-20  

------------------------------------------------------------------------

## 1. Purpose

### Phase 11 Alignment

The Research Agent interfaces are designed to operate within the
Project0 Dashboard Framework. The Dashboard Framework provides the
browser-based user interface, navigation, shared layout, and template
infrastructure, while Research Agent interfaces define only the
contracts between Research Agent components. The Dashboard Framework
remains architecturally separate from Research Agent business logic.

The Research Agent workflow adds human-in-the-loop research interactions
hosted within the Dashboard Work Area. The Dashboard Framework continues
to provide the shared application shell, navigation, and hosting
infrastructure. Research Agent interfaces define only agent-specific
workflow interactions, including research request processing, research
strategy generation, external research source access, paper metadata
retrieval, research evaluation, research artifact generation, and
workflow result handling.

Research request processing supports optional research constraints,
focus areas, and user-provided papers or references. When these inputs
are not provided, the Research Agent workflow uses the research question
and available Project0 services to develop an appropriate research
strategy. Agent interfaces remain independent of the specific search,
source selection, ranking, and evaluation strategies used by the
underlying services.

External research source access is isolated behind Research Agent
interfaces so that source-specific implementations remain separate from
Research Agent workflow behavior. Citation and source information are
preserved through interface contracts so that generated research
artifacts remain traceable to identifiable research sources.

Agent-specific UI behavior and presentation details remain outside these
interfaces and are implemented by the Research Agent UI components.

------------------------------------------------------------------------

## Research Source Provider Interface Contract

The Research Agent isolates external research source implementations
through Research Source interfaces.

The interface contract allows the Research Workflow and Research Source
Service to depend on source capabilities rather than specific external
provider implementations.

Initial provider implementations include:

-   Semantic Scholar Source Provider
    -   Supports production research source retrieval.
    -   Provides identifiable research source references for downstream
        metadata retrieval and evaluation.
-   Stub Research Source Provider
    -   Supports deterministic research workflow validation.
    -   Provides controlled research source behavior for testing,
        demonstrations, and acceptance workflows.

Research source providers preserve source identifiers and citation
information through the shared interface contracts.

Provider interaction model:

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

The interface contract allows additional research sources to be added
without modifying Research Agent workflow behavior.

------------------------------------------------------------------------

## Research Query Interface Contract

The Research Agent separates research intent definition from external
research source execution through a dedicated Research Query interface.

The Research Query interface transforms a structured Research Strategy
into deterministic, provider-ready research queries.

Responsibilities:

-   Accept structured research strategies.
-   Generate focused research queries from research concepts.
-   Preserve deterministic query ordering.
-   Remove duplicate query terms.
-   Remain independent from external research source implementations.
-   Provide query results to the Research Source Service for downstream
    source execution.

Provider interaction model:

``` text
Research Workflow
        |
        v
Research Strategy Service
        |
        v
Research Query Interface
        |
        v
Research Source Service
        |
        v
Research Source Provider Interface
```

The interface contract allows query generation behavior to evolve
without modifying external research source implementations or workflow
coordination behavior.

------------------------------------------------------------------------

------------------------------------------------------------------------

## Revision Workflow Interface Behavior

Research Agent interfaces support revision of generated research
requests and research outputs through the workflow interaction contract.

Revision behavior includes:

-   returning a user to an editable request state
-   preserving the original research request
-   preserving optional research constraints
-   preserving source and citation information
-   accepting updated or appended user instructions
-   submitting the revised request through the existing research
    workflow

The interface contract does not determine research source selection,
search strategy, relevance evaluation, or UI presentation details. Those
responsibilities remain with the Research Agent workflow services and
Research Agent UI components.
