# Research Agent Architecture

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This document describes the implemented component organization and runtime
flow of the Project0 Research Agent. Algorithmic rules and exact limits are
defined in the Research Agent Design.

---

## 2. Architectural Principles

- Agent-specific behavior remains under `project0.agents.research`.
- The Dashboard supplies the shared shell; the Research Agent supplies its
  routes, template, presentation models, and UI adapter.
- The Platform Dispatcher is the composition and invocation boundary.
- Typed protocols and immutable dataclasses define component contracts.
- Deterministic services control parsing, query selection, dispatch,
  deduplication, ranking boundaries, validation, and presentation mapping.
- Reasoning providers receive explicit JSON schemas for AI-assisted stages.
- Research findings remain distinguishable from source metadata and evidence.
- Partial evidence and recoverable generated-output defects are represented
  explicitly rather than silently upgraded to supported conclusions.

---

## 3. Runtime Topology

`create_project0_dashboard_app()` creates separate Documentation and Research
dispatchers so each agent can use its configured model name. In normal Ollama
mode the two dispatchers share one `OllamaReasoningProvider` instance. The
Research dispatcher constructs the complete Research Workflow.

~~~mermaid
flowchart TD
    UI["Research Agent UI"]
    PD["Platform Dispatcher"]
    RW["Research Workflow"]
    S["Strategy and Query"]
    R["Provider Retrieval"]
    E["Metadata and Evidence"]
    A["Evaluation and Analysis"]
    O["Result and Browser View"]

    UI --> PD
    PD --> RW
    RW --> S
    S --> R
    R --> E
    E --> A
    A --> O
~~~

The Research Workflow is synchronous. The browser displays a client-side
processing state while the POST request runs in a Starlette thread pool; it
does not receive per-stage server progress events.

---

## 4. Workflow Sequence

~~~mermaid
flowchart TD
    C["Optional context ingestion"]
    X["Context analysis"]
    Q["Strategy and bounded queries"]
    D["Provider discovery and balancing"]
    M["Metadata and evidence shortlist"]
    V["Final evaluation"]
    P["Retained-paper analysis"]
    R["Direction analysis"]
    Z["Result, legacy artifacts, UI"]

    C --> X
    X --> Q
    Q --> D
    D --> M
    M --> V
    V --> P
    P --> R
    R --> Z
~~~

When no context file is supplied, the workflow starts at strategy generation.
When fewer than two valid paper analyses exist, Direction Analysis is skipped.
When Direction Analysis fails validation twice or its provider fails, the
workflow continues with a warning. Other expected service failures produce a
failed `ResearchResult`.

---

## 5. Components

### Research Agent routes

`research_agent_routes.py` defines:

- `GET /agents/research` for the ready page; and
- `POST /agents/research/request` for question, guidance, Maximum Results, and
  optional file upload.

The POST handler reads upload bytes, delegates blocking work through
`run_in_threadpool`, and renders the returned page state.

### Research Agent UI Service and view models

The UI Service validates the non-empty question, delegates to the Platform
Dispatcher, maps `ResearchResult` into immutable browser models, consolidates
paper metadata/evaluation/analysis by source identity, merges evaluation
warnings into displayed relevance limitations, and derives the page status.

### Platform Dispatcher

The dispatcher exposes `run_research_workflow`, constructs `ResearchRequest`,
and delegates to the configured Research Workflow. The composition root wires
all current research services, selected source providers, and the
agent-specific model name.

### Context Ingestion Service

This deterministic service accepts UTF-8 Markdown/text and text-extractable
PDFs. It extracts PDF text with pypdf. It does not perform OCR, chunking, or
persistent source-document storage.

### Existing Research Context Analysis Service

This reasoning-backed service converts all extracted text into structured
findings with context-document provenance. It also returns three distinct
solution-search concepts when a question is supplied. Structural or
traceability failures receive one retry.

### Research Strategy Service

This deterministic service derives the objective, concepts, seed terms,
sub-questions, constraints, source names, rationale, and context-inferred
solution concepts.

### Research Query Service

This deterministic, provider-independent service preserves seeds, derives
complementary search dimensions, removes duplicates and high-overlap queries,
and returns at most three discovery queries in addition to up to three seeds.

### Research Source Service

This service dispatches each query to each configured provider, tolerates
individual provider/query runtime failures when any other result succeeds,
deduplicates publication versions, optionally applies the current
alignment-oriented eligibility profile, preserves seeds, and round-robins
ranked results across provider/query groups into a default 24-candidate pool.

It records summary statistics and a DEBUG candidate trace. It does not call the
reasoning provider.

### Source providers

The provider protocol accepts a `ResearchStrategy` and returns normalized
`ResearchSourceReference` objects. Implemented providers are Semantic Scholar,
OpenAlex, OpenReview, Crossref, arXiv, and stub. The default active pair is
Semantic Scholar and arXiv.

### Paper Metadata Service

This service normalizes provider metadata. For Semantic Scholar records it
attempts a detail request with retry and falls back to search metadata on
exhausted HTTP failures.

Its evidence phase accepts at most eight papers, adds available abstracts, and
attempts bounded extraction of selected PDF sections from provider-supplied
open-access locations.

### Research Evaluation Service

This reasoning-backed service performs preliminary or final evaluation in
batches of three. It validates opaque batch-local IDs, score shape, full batch
coverage, and contradictory high-score statements. It recovers valid partial
items, retries unresolved papers once, and produces unscored records for
persistent retryable defects.

### Research Workflow selection

The workflow preliminarily ranks metadata when more than eight candidates are
available. The current evidence-candidate selector uses explicit direct and
transferable visual-language representation/alignment tiers, then score order.
This selector is implementation-specific and does not represent a generic
domain-independent ranking architecture.

After final evaluation, only papers with evidence sections remain in the
default path. They are sorted by score and limited by the request. Papers below
the 0.75 recommendation threshold may remain as reviewed results.

### Paper Analysis Service

This reasoning-backed service analyzes each retained paper independently.
Every accepted finding cites a supplied evidence section and page when
available. A retryable structural failure is retried once; a persistent
structural failure skips only that paper.

### Research Direction Analysis Service

This reasoning-backed service uses at most three valid paper analyses and the
optional context. It creates opaque evidence handles, validates returned
provenance, requires cross-paper evidence for most synthesis categories, and
enforces context/literature grounding for candidate directions. Unsupported
ordinary synthesis items are omitted. Certain semantic grounding failures
invalidate and retry the full response.

### Research Artifact Service

The service produces three legacy in-memory artifacts—literature comparison,
research gap, and experiment proposal—when evaluations exist. These artifacts
have empty `source_references` and are intentionally not rendered by the
current template.

The visible **Save Results** behavior is separate: browser JavaScript builds
`project0_research_results.md` from the rendered consolidated package.

---

## 6. Data Contracts

The principal immutable models are:

- `ResearchRequest` and `ResearchStrategy`;
- `ResearchSourceReference` and `PaperMetadata`;
- `ResearchPaperEvidenceSection` and evidence status/basis enums;
- `ResearchContextDocument` and `ExistingResearchContext`;
- `ResearchEvaluation` and `PaperAnalysis`;
- `ResearchSynthesis`, `ResearchDirection`, and
  `ResearchDirectionAnalysis`;
- `ResearchArtifact`; and
- `ResearchResult`.

Provider-neutral reasoning uses `ProviderRequest` and `ProviderResponse`.
Service protocols reside in `research_interfaces.py`; source providers use the
separate `ResearchSourceProviderProtocol`.

---

## 7. Reasoning Provider Architecture

Research reasoning services depend on `ReasoningProviderProtocol.generate`,
not directly on Ollama. The production Dashboard composition supports:

- `ollama`, which posts system/user messages and the requested JSON schema to
  `/api/chat` with streaming disabled; and
- `stub`, used for deterministic development and test paths.

The Research Agent model defaults to `qwen2.5:7b` and can be overridden
independently of the Documentation Agent model. Each research reasoning stage
requests temperature 0.0. The provider uses the configured timeout unless a
request supplies a positive `timeout_seconds` metadata override.

---

## 8. Validation Boundaries

The Research Workflow does not invoke the reusable Markdown/Link/MkDocs
`ValidationService`. Research validation is implemented inside the context,
evaluation, paper-analysis, and direction-analysis services as typed parsing,
coverage checks, evidence resolution, and semantic guardrails.

This distinction is important: Research Agent output validation is real, but it
is not the Documentation Agent's artifact-validation pipeline.

---

## 9. External Dependencies

- FastAPI, Starlette, Jinja2, and Uvicorn for the local browser application.
- httpx for source, metadata, PDF, and Ollama HTTP calls.
- pypdf for context and paper PDF text extraction.
- Configured research-provider APIs.
- A local Ollama service and installed model in default reasoning mode.
- pytest and Playwright for automated verification.

---

## 10. Architectural Constraints

- Execution is synchronous and local-first.
- No context chunking or OCR is implemented.
- Retrieval and evidence bounds limit coverage.
- The alignment-specific candidate heuristics can affect non-ECE research
  whenever their trigger vocabulary is present.
- Provider failures that are masked by other successful result groups are
  logged but not surfaced as workflow warnings.
- Direction Analysis uses at most three paper analyses.
- Legacy artifacts and client-saved Markdown are separate output mechanisms.
- Human review of the underlying papers remains required.

---

## 11. Future Expansion

Potential future changes include asynchronous execution, progress events,
generic configurable candidate profiles, additional providers, caching,
context chunking, OCR, richer evidence extraction, source-failure reporting,
and citation-aware export formats. These are not current behavior.

