# Research Agent Interface Design

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This document defines the implemented browser, dispatcher, service, provider,
model, and presentation interfaces of the Project0 Research Agent.

---

## 2. Browser Interface

### Routes

| Method | Route | Name | Behavior |
| --- | --- | --- | --- |
| GET | `/agents/research` | `research_agent_home` | Renders the ready Research Agent Work Area. |
| POST | `/agents/research/request` | `research_agent_submit_request` | Reads form/upload values, executes the UI service in a thread pool, and renders the resulting page. |

Research Agent routes must be registered before the Dashboard's generic
`/agents/{agent_identifier}` placeholder.

### Form

| Field | Browser control | Required | Values |
| --- | --- | --- | --- |
| Existing research context | file | no | `.pdf`, `.md`, `.markdown`, `.txt` |
| Research question | textarea | yes | non-empty after trimming |
| Research guidance | textarea | no | free-form text |
| Maximum Results | select | yes | 5, 10, 15, 20; default 10 |

The HTML `required` attribute provides client validation. Server-side UI
validation also prevents a blank question from invoking the workflow.

### Page states

`ResearchAgentPageStatus` values are:

- `ready`
- `processing`
- `completed`
- `completed_with_warnings`
- `failed`

`processing` is used when a mapped result has no recognized final status. On
normal form submission, JavaScript immediately disables the submit button,
shows “Searching and evaluating research...”, identifies the active operation
as “Research Workflow”, and starts elapsed-time/status updates while awaiting
the synchronous POST response.

### Visible results

The template can render:

- workflow status and warnings;
- the populated request form;
- uploaded context filename and Existing Research Context Analysis;
- consolidated Research Results cards;
- Research Direction Analysis;
- Workflow Summary counts; and
- shared system status for the Research Agent model and GPU.

The visible workflow-progress labels are Request, Strategy, Source Search,
Metadata, Evaluation, Artifacts, and Complete. They are presentation states,
not server-emitted per-stage events.

Separate paper-analysis and legacy artifact panels remain disabled in the
template. Available paper analysis is embedded in each consolidated card.

### Save Results

The button appears when results are present and the page is completed or
completed-with-warnings. Client JavaScript serializes the visible result
package to `project0_research_results.md`. It attempts
`showSaveFilePicker` first and falls back to a Blob download.

---

## 3. UI Service Contract

`ResearchAgentUIService` depends on a minimal `ResearchWorkflowPort`:

~~~python
run_research_workflow(
    question: str,
    guidance: str = "",
    max_results: int = 10,
    context_source_name: str | None = None,
    context_content: bytes | None = None,
) -> object
~~~

The UI adapter deliberately reads either attributes or mapping keys so tests
and alternate ports can supply compatible objects.

### Mapping rules

- Missing optional values become empty tuples or nulls.
- Unknown workflow-status strings map to no workflow status and therefore a
  processing page unless warnings/errors determine another state.
- A returned error message or `ResearchStatus.FAILED` yields a failed page.
- Workflow warnings are preserved at page level.
- Evaluation warnings are combined with evaluation limitations on the card.
- Papers, evaluations, source references, and analyses are joined by source
  identity while preserving evaluation order.
- An `abstract_metadata` analysis is hidden when the displayed paper has no
  abstract.
- Null-like optional finding text is omitted.

---

## 4. Platform Dispatcher Interface

`PlatformDispatcher.run_research_workflow` exposes:

~~~python
run_research_workflow(
    question: str,
    guidance: str = "",
    max_results: int = 10,
    context_source_name: str | None = None,
    context_content: bytes | None = None,
) -> ResearchResult
~~~

The dispatcher rejects an empty question, creates `ResearchRequest`, and calls
`ResearchWorkflow.execute`. Browser users normally encounter the earlier UI
validation rather than the dispatcher exception.

`ResearchWorkflowProtocol.execute` accepts the request plus the paired optional
context filename and bytes.

---

## 5. Service Protocols

The Research Agent defines protocols for:

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

The workflow also detects `rank_candidates` dynamically on the evaluation
service and falls back to `evaluate` for preliminary ranking. It detects
`acquire_evidence` dynamically on the metadata service to preserve a legacy
workflow path for compatible test doubles/implementations.

---

## 6. Source Provider Interface

`ResearchSourceProviderProtocol.search(strategy)` returns an ordered tuple of
`ResearchSourceReference`.

Provider configuration names are exact lowercase tokens:

~~~text
semantic_scholar
openalex
openreview
crossref
arxiv
stub
~~~

The Provider Factory returns a dictionary keyed by the selected names. Unknown
names raise `ValueError`.

Each normalized source reference contains:

- provider `source_name`;
- provider `source_id`;
- title;
- optional URL;
- authors;
- optional publication year; and
- provider-specific metadata.

---

## 7. Reasoning Provider Interface

Context Analysis, Evaluation, Paper Analysis, and Direction Analysis depend on
`ReasoningProviderProtocol.generate(ProviderRequest) -> ProviderResponse`.

`ProviderRequest` carries system instructions, JSON user prompt, JSON response
schema, model name, temperature, optional output-token bound, request metadata,
and request ID. `ProviderResponse.structured_output` must be a mapping for the
Research Agent parsers.

The Ollama implementation posts:

~~~json
{
  "model": "<request model>",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "stream": false,
  "format": {"type": "object"},
  "options": {"temperature": 0.0}
}
~~~

The actual `format` value is the complete service-supplied response schema.
The provider parses the returned message content as JSON and returns a
provider-neutral response. HTTP, response-shape, and JSON errors are explicit.

---

## 8. Data Model Interfaces

### Request and strategy

`ResearchRequest` includes question, guidance, Maximum Results, programmatic
constraints/focus areas/source names, metadata, and request ID.

`ResearchStrategy` includes concepts, search terms, seeds, objective,
sub-questions, constraints, source names, rationale, and inferred
solution-search concepts.

### Source, metadata, and evidence

`ResearchSourceReference` preserves discovery identity and metadata.
`PaperMetadata` preserves normalized metadata plus:

- `ResearchPaperEvidenceStatus.AVAILABLE` or `DISCOVERY_ONLY`; and
- zero or more `ResearchPaperEvidenceSection` values with section, content, and
  optional page.

`ResearchPaperAnalysisBasis` distinguishes `ABSTRACT_METADATA`,
`PAPER_CONTENT`, and the model-defined `DISCOVERY_ONLY` value. Current
`PaperAnalysisService` returns only the first two because evidence-free papers
are skipped.

### Findings and analyses

`ResearchEvidenceReference` identifies a context document or research paper
and may include page/section. `ResearchFinding` couples content to evidence.
These compose Existing Research Context, Paper Analysis, Research Synthesis,
and Research Direction models.

### Result

`ResearchResult` contains:

- request ID, status, summary, creation time;
- strategy;
- source references, papers, evaluations, and legacy artifacts;
- optional Existing Research Context;
- paper analyses;
- optional Direction Analysis;
- warnings and error message; and
- metadata such as source-search and evidence-review statistics.

Statuses are `pending`, `completed`, `completed_with_warnings`, and `failed`.
The workflow returns only completed, completed-with-warnings, or failed.

---

## 9. Evidence and Structured-Output Contracts

### Evaluation

Provider evaluation identifiers are generated as `paper-NNN` per batch and
must be returned exactly once. Scores are integer 0–100 or null and are
normalized internally. Retryable identity/coverage/high-score defects receive
one partial retry.

### Paper analysis

The provider does not return a paper ID. Each finding returns non-empty content,
section, and page number. Section/page must match supplied evidence.

### Direction analysis

The provider may return only enumerated opaque context/literature handles.
Accepted handles resolve to original `ResearchEvidenceReference` objects.
Synthesis and candidate-direction grounding rules are enforced after schema
generation; JSON schema alone is not the complete contract.

---

## 10. System Status Interface

`GET /api/system-status?agent=research` returns:

~~~json
{
  "llm_provider": "...",
  "llm_model": "...",
  "gpu_name": "...",
  "gpu_utilization": "...",
  "gpu_vram": "..."
}
~~~

For a non-Ollama provider, the model is reported as “Not applicable”. GPU
fields are “Unavailable” when `nvidia-smi` cannot provide data.

---

## 11. Interface Safety

- Uploaded context bytes and filename must be paired.
- No Research Agent interface mutates the repository.
- External source IDs are not trusted as provider-returned evaluation handles.
- Generated evidence handles are resolved only against the supplied catalog.
- Missing information remains absent, unscored, warned, or failed according to
  the relevant service contract.
- Client-saved Markdown is a user download, not a repository write.

