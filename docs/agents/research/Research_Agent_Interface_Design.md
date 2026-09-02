# Research Agent Interface Design

**Version:** 0.3  
**Owner:** Project0  
**Last Updated:** 2026-09-02

---

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
strategy generation, optional Existing Research Context processing,
external research source access, paper metadata retrieval, research
evaluation, per-paper analysis, research direction analysis, research
artifact generation, and workflow result handling.

Research request processing supports optional research constraints,
focus areas, user-provided papers or references, and an optional Existing
Research Context document. When these inputs are not provided, the
Research Agent workflow uses the research question and available Project0
services to develop an appropriate research strategy. When an Existing
Research Context document is not provided, existing workflow semantics
and result behavior are preserved. Agent interfaces remain independent
of the specific search, source selection, ranking, and evaluation
strategies used by the underlying services.

External research source access is isolated behind Research Agent
interfaces so that source-specific implementations remain separate from
Research Agent workflow behavior. Multiple configured research source
providers may contribute references through the same interface contract.
Citation and source information are preserved through interface
contracts so that generated research artifacts remain traceable to
identifiable research sources.

Agent-specific UI behavior and presentation details remain outside these
interfaces and are implemented by the Research Agent UI components.

The Phase 10 Research Agent implementation validated these interface
contracts through unit, integration, and acceptance testing while
preserving separation between Research Agent workflow behavior and
shared Project0 platform infrastructure.
---

## Existing Research Context Interface Contract

The Research Agent supports an optional Existing Research Context
document through defined context ingestion and analysis interfaces.

Context document interaction uses a simple file-selection/upload
mechanism. Supported initial document types are text-based PDF, Markdown,
and plain text. The Research Agent does not store a copy of the selected
source document.

Responsibilities:

-   Accept an optional Existing Research Context document.
-   Extract text content from supported document types.
-   Preserve page- or section-level source provenance.
-   Support bounded document chunking with implementation limits to be
    defined.
-   Clearly report context extraction or analysis failures.
-   Reject image-only or scanned PDF documents requiring OCR.
-   Produce structured Existing Research Context containing the research
    problem, prior work, implemented approaches, findings, limitations,
    unresolved questions, stated future work, and source references.

When context processing succeeds, the structured Existing Research
Context is provided to research strategy generation and downstream
research analysis. Open-ended research requests are supported when
Existing Research Context is available.

Context findings are source-derived and remain distinguishable from
generated analysis.

---

## Per-Paper Analysis Interface Contract

The Per-Paper Analysis interface defines structured technical analysis
for each retained paper.

Responsibilities:

-   Identify the paper problem and approach.
-   Identify representations and modalities.
-   Identify the learning or alignment objective.
-   Identify datasets or tasks.
-   Identify findings and limitations.
-   Explain relevance to the current research.
-   Preserve evidence references.
-   Identify analysis derived from metadata and abstract information.

Per-paper analysis is source-derived interpretation and remains
distinguishable from source information and Research Agent inference.

---

## Research Direction Analysis Interface Contract

The Research Direction Analysis interface defines cross-paper analysis
and evidence-grounded candidate research direction generation.

Responsibilities:

-   Accept optional Existing Research Context and retained Paper
    Analyses.
-   Produce structured synthesis findings containing themes,
    comparisons, shared limitations, and unresolved questions.
-   Identify candidate research directions.
-   Preserve context motivation and literature evidence for candidate
    directions unless explicitly marked speculative.
-   Preserve provenance for referenced context items and papers.

Cross-paper synthesis remains functionality within Research Direction
Analysis rather than a separate interface. Research directions are
Research Agent inference grounded in source-derived context and
per-paper interpretation.

The output contract includes synthesis findings and candidate research
directions. Validation rejects unknown context items or paper identifiers,
and requires both context motivation and literature evidence for each
non-speculative candidate direction.

---

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
-   arXiv Source Provider
    -   Supports external research source retrieval through arXiv.
-   Crossref Source Provider
    -   Supports external research source retrieval through Crossref.
-   OpenAlex Source Provider
    -   Supports external research source retrieval through OpenAlex.
-   OpenReview Source Provider
    -   Supports external research source retrieval through OpenReview.
-   Stub Research Source Provider
    -   Supports deterministic research workflow validation.
    -   Provides controlled research source behavior for testing,
        demonstrations, and acceptance workflows.

Research source providers preserve provider-specific source
identifiers and citation information through the shared interface
contracts.

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

The interface contract allows additional research sources to be added
or configured together without modifying Research Agent workflow
behavior.

---

## Research Query Interface Contract

The Research Agent separates research intent definition from external
research source execution through a dedicated Research Query interface.

The Research Query interface transforms a structured Research Strategy
into deterministic, provider-ready research queries.

Responsibilities:

-   Accept structured research strategies.
-   Generate focused research queries from research concepts.
-   Generate a complementary, bounded query set from the Research
    Strategy, optional Existing Research Context, and user guidance.
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

---

---

## Research Analysis Validation Interface Behavior

Research analysis interfaces preserve traceability between generated
analysis and supporting source information.

Validation behavior includes:

-   verifying that referenced context items exist
-   verifying that referenced paper identifiers exist
-   verifying candidate research direction context motivation and
    literature evidence unless explicitly marked speculative
-   rejecting unknown source identifiers
-   preserving the distinction between source-derived context findings,
    source-derived per-paper interpretation, and Research Agent inference

Saved research package interfaces include the request, context summary,
research strategy, retained papers, per-paper analyses, synthesis
findings, candidate directions, provenance, and validation status.

---

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
