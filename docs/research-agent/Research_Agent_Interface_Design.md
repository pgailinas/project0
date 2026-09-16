# Research Agent Interface Design

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

This document defines the implemented browser, dispatcher, service, provider, model, presentation, status, and safety interfaces of the Project0 Research Agent. It describes public boundaries and contracts rather than internal algorithms.

## 2. Interface Boundaries

The Research Agent separates browser routes and forms, the UI adapter, the Platform Dispatcher, workflow/service protocols, research-source providers, reasoning providers, immutable domain models, and presentation models. Research routes must be registered before the Dashboard's generic `/agents/{agent_identifier}` route.

The browser and UI validate and map requests but do not implement retrieval, evidence evaluation, or research reasoning. The Platform Dispatcher constructs `ResearchRequest` and invokes `ResearchWorkflowProtocol.execute`. Research services depend on protocols, and external source/provider identifiers remain distinct from generated batch-local evidence handles.

## 3. Interface Contracts

### Browser

| Method | Route | Behavior |
| --- | --- | --- |
| `GET` | `/agents/research` | Render the ready Work Area. |
| `POST` | `/agents/research/request` | Read form/upload values, run the UI service in a thread pool, and render the result. |

The form accepts optional `.pdf`, `.md`, `.markdown`, or `.txt` context; a required nonblank question; optional guidance; and Maximum Results of 5, 10, 15, or 20 with 10 as default. Client and server validation prevent blank questions from invoking the workflow.

Page states are `ready`, `processing`, `completed`, `completed_with_warnings`, and `failed`. JavaScript disables submission, shows the Research Workflow operation and elapsed time, and polls status while awaiting the synchronous response; displayed progress labels are presentation states, not server stage events.

The page may show request values, context filename/findings, consolidated paper cards, Direction Analysis, summary counts, warnings, model, and GPU. Embedded paper analyses appear in cards; separate analysis and legacy-artifact panels remain disabled. **Save Results** serializes the visible completed package to `project0_research_results.md` using `showSaveFilePicker` or Blob download.

### UI and dispatcher

`ResearchAgentUIService` and `PlatformDispatcher.run_research_workflow` expose compatible operations:

```python
run_research_workflow(
    question: str,
    guidance: str = "",
    max_results: int = 10,
    context_source_name: str | None = None,
    context_content: bytes | None = None,
) -> object
```

The dispatcher returns `ResearchResult`; the UI port intentionally accepts an object and maps attributes or keys for test/adapter compatibility. The dispatcher rejects blank questions. `ResearchWorkflowProtocol.execute` accepts `ResearchRequest` plus paired optional context name and bytes.

Mapping preserves workflow warnings, joins papers/evaluations/sources/analyses by source identity in evaluation order, combines evaluation warnings with limitations, hides abstract-only analysis when no abstract exists, omits null findings, defaults missing optional collections to empty, and maps errors or failed status to a failed page. Unknown result status otherwise maps to processing.

### Service and provider protocols

| Protocol | Principal operation |
| --- | --- |
| `ResearchContextIngestionServiceProtocol` | `ingest(source_name, content)` |
| `ExistingResearchContextAnalysisServiceProtocol` | `analyze(document, research_question="")` |
| `ResearchStrategyServiceProtocol` | `build_strategy(request, context=None)` |
| `ResearchQueryServiceProtocol` | `generate_queries(strategy)` |
| `ResearchSourceServiceProtocol` | `search(strategy)` |
| `PaperMetadataServiceProtocol` | `retrieve_metadata(references)` and `acquire_evidence(papers)` |
| `ResearchEvaluationServiceProtocol` | `evaluate(request, strategy, papers)` |
| `PaperAnalysisServiceProtocol` | `analyze(request, strategy, papers)` |
| `ResearchDirectionAnalysisServiceProtocol` | `analyze(request, context, paper_analyses)` |
| `ResearchArtifactServiceProtocol` | `generate_artifacts(request, evaluations)` |
| `ResearchWorkflowProtocol` | `execute(request, context_source_name=None, context_content=None)` |

The workflow dynamically detects `rank_candidates` and `acquire_evidence` to support compatible legacy implementations. `ResearchSourceProviderProtocol.search(strategy)` returns ordered `ResearchSourceReference` values. Exact provider tokens are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`; unknown names raise `ValueError`.

Reasoning-backed services call `ReasoningProviderProtocol.generate(ProviderRequest) -> ProviderResponse`. Requests carry instructions, JSON prompt/schema, model, temperature, optional token bound, metadata, and request ID. `structured_output` must be a mapping. Ollama posts non-streaming `/api/chat` with the complete supplied schema and temperature 0.0; HTTP, response-shape, and JSON errors remain explicit.

## 4. Data and Error Contracts

`ResearchRequest` represents question, guidance, limits, programmatic constraints/focus/sources, metadata, and ID. `ResearchStrategy` represents concepts, terms, seeds, objective, sub-questions, constraints, sources, rationale, and inferred concepts. Source, metadata, and evidence models preserve discovery identity, normalized fields, `AVAILABLE`/`DISCOVERY_ONLY` state, section content, and optional pages.

Evidence references identify context documents or papers plus optional page/section. Findings couple content to evidence and compose context, paper, synthesis, and direction models. `ResearchResult` contains ID, status, summary, time, strategy, sources, papers, evaluations, legacy artifacts, optional context, analyses, optional Direction Analysis, warnings/errors, and statistics. Status values are `pending`, `completed`, `completed_with_warnings`, and `failed`; the workflow returns the final three.

Evaluation handles are batch-local `paper-NNN` values returned exactly once with integer 0–100 or null scores. Paper-analysis findings must cite supplied section/page. Direction output may cite only enumerated context/literature handles, which resolve to original evidence; schema validation is supplemented by semantic grounding checks.

`GET /api/system-status?agent=research` returns `llm_provider`, `llm_model`, `gpu_name`, `gpu_utilization`, and `gpu_vram`. A non-Ollama model is “Not applicable”; unavailable NVIDIA data is “Unavailable”.

## 5. Guarantees and Limitations

- Context bytes and filename must be paired.
- No Research Agent interface mutates the repository.
- External IDs are not accepted as generated evaluation handles.
- Evidence handles resolve only against the supplied catalog.
- Missing information remains absent, unscored, warned, or failed under the relevant contract.
- Client-saved Markdown is a user download, not a repository write.
- Browser progress is not server-emitted stage telemetry.
- Dynamic legacy-method detection preserves compatible test doubles but does not broaden the documented primary contracts.
