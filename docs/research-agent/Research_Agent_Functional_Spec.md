# Research Agent Functional Specification

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

This specification defines the implemented inputs, processing behavior, outputs, configuration, and failure handling of the Project0 Research Agent. The agent performs bounded, multi-provider technical-literature discovery and evidence-grounded analysis; it does not provide exhaustive coverage, independently verify scientific claims, or establish novelty.

## 2. Functional Requirements

### Strategy and query generation

The agent shall construct a deterministic strategy containing the research objective, ordered concepts, up to three explicit publication seeds, sub-questions, constraints, configured sources, rationale, and solution-search concepts inferred from Existing Research Context. Existing-project findings, limitations, unresolved questions, stated future work, and research-problem prose shall remain context evidence and shall not be copied into literature-search concepts. With a research question, context analysis must return exactly three concepts, each identifying a source representation or model, target model or space, and distinct mechanism. Explicit model, encoder, or decoder anchors omitted by reasoning output shall be restored.

The Query Service shall preserve exact seeds first, create at most three discovery queries, emit at most six total terms, normally limit discovery queries to eight words, remove exact and substantially overlapping queries, and select complementary direct, mechanism, transfer, and application roles when available. Query generation is deterministic and provider-independent.

### Retrieval, consolidation, and balancing

Supported provider names are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`; configured providers determine which are active. Each active provider is called once per query in provider and query order. Crossref is skipped for an arXiv-only identifier or URL.

Duplicates match by provider/source identifier, normalized DOI or arXiv identifier, or normalized title with compatible year and overlapping authors when both author sets exist. The richest record becomes canonical and complementary metadata is merged. Explicit seeds are preserved first; remaining candidates are ranked within provider/query groups and selected round-robin to the default 24-candidate evaluation limit.

For strategies containing visual, language, and alignment-mechanism anchors, the implemented eligibility profile shall retain preserved seeds and non-seed candidates with either a direct video-language representation-alignment path or a transferable visual-language representation-alignment mechanism. Generic lexical matches that do not establish that complete path, unrelated modalities or tasks, and representation-learning synthesis/generation candidates shall be excluded. This heuristic is not a general relevance guarantee.

### Metadata, evidence, and evaluation

Metadata shall be normalized for every supported provider. Semantic Scholar uses a detail request with search-result fallback after exhausted HTTP failures; other providers use normalized search metadata.

After the single evaluation retry, an otherwise valid result whose integer score is exactly one point outside its declared mechanism band shall be corrected to the nearest boundary and annotated with a warning. Larger score-band contradictions and any result failing another structural or evidence validation remain unscored.

When configured providers do not return an exact match for an explicit modern arXiv guidance seed, source selection shall synthesize a canonical arXiv reference from the supplied identifier. The fallback retains seed provenance and canonical abstract/PDF URLs; it does not invent title, author, abstract, or evaluation evidence.

When more than eight candidates reach evidence processing, preliminary metadata ranking shall select at most eight. Evidence acquisition may include abstracts and provider-authoritative or derived arXiv PDFs. Retrieved content must be a PDF. Recognized Abstract, Method/Methodology/Approach/Model, and Experiment/Results/Evaluation sections are extracted with page provenance, an 8,000-character section limit, and 24,000-character total limit. Retrieval or extraction failure falls back to an available abstract; a paper without usable evidence is `discovery_only`.

Final evaluation shall use batches of no more than three and opaque batch-local identifiers. Scores are integers from 0 through 100 or null, normalized to 0.0 through 1.0; 0.75 is the recommendation threshold. When deterministic paper evidence changes a mechanism classification, the resulting summary, structured mechanism fields, connection, and applicable limitations shall agree with the corrected classification. Unrelated limitations shall remain. Missing, duplicate, corrupt, invented, or contradictory-high-score entries are retried once while valid partial results are retained. Persistent unresolved papers become unscored invalid-response evaluations. Non-retryable schema/type errors and provider failures propagate.

Evidence-free and persistently unscored papers are excluded from final selection. Scored, evidence-reviewed results are sorted by descending score and limited by Maximum Results. Adjacent reviewed evidence may fill remaining result slots and is not removed solely for scoring below 0.50 or below the 0.75 recommendation threshold.

### Analysis and presentation

Each retained paper with usable evidence shall be analyzed independently. Problem and approach are required; representations, modalities, objectives, datasets/tasks, findings, limitations, and warnings are optional. Findings must cite supplied evidence and page numbers when present. A structurally invalid response is retried once; persistent structural failure skips that analysis, while a provider exception fails the workflow.

Research Direction Analysis is enabled by default when configured and at least two valid paper analyses exist. It receives at most three analyses, uses opaque evidence handles, requires cross-paper findings to cite at least two papers, restricts performance ordering to directly supported claims, and enforces context/literature grounding for candidate directions. Invalid items may be omitted; semantic grounding or direction-structure errors cause one full retry. Persistent failure produces a warning and omits Direction Analysis.

The browser shall present workflow status, warnings, request values, context filename and findings, consolidated retained-paper cards, available analyses, Direction Analysis, and source/evaluation counts. **Save Results** shall create `project0_research_results.md` from the visible package. Legacy in-memory artifacts remain in the result model but are not rendered.

## 3. Inputs and Outputs

### Inputs

- A nonblank research question is required and trimmed by the UI; blank browser input fails before workflow execution.
- Research Guidance is optional. It is deterministically parsed into constraints, sub-questions, ordered concepts, and up to three quoted-title, arXiv, or DOI seeds.
- Browser Maximum Results choices are 5, 10, 15, and 20, with 10 as default. Final slicing uses `max(1, max_results)`; arbitrary programmatic values are otherwise not validated by the Platform Dispatcher.
- Existing Research Context may be UTF-8 `.md`, `.markdown`, or `.txt`, or a text-extractable `.pdf`. Filename and bytes must be paired. Empty, unsupported, invalid, malformed, or image-only inputs fail. OCR and chunking are not implemented; extracted text is sent in one reasoning request.

### Outputs

`ResearchResult` shall contain status, summary, strategy, selected sources, retained papers and evaluations, compatibility artifacts, optional Existing Research Context, paper analyses, optional Direction Analysis, warnings, and source/evidence-review statistics.

Successful status is `completed` or `completed_with_warnings`; handled failures return `failed`.

### Runtime configuration

| Environment variable | Default | Behavior |
| --- | --- | --- |
| `PROJECT0_REASONING_PROVIDER` | `ollama` | Dashboard accepts `ollama` or `stub`. |
| `PROJECT0_RESEARCH_SOURCE_PROVIDERS` | `semantic_scholar,arxiv` | Active, case-sensitive provider names. |
| `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS` | `True` | Only `1`, `true`, `yes`, and `on` enable. |
| `PROJECT0_RESEARCH_OLLAMA_MODEL` | `PROJECT0_OLLAMA_MODEL` or `qwen2.5:7b` | Research model. |
| `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` | Shared fallback model. |
| `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API URL. |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | `600.0` | Default request timeout. |
| `PROJECT0_SEMANTIC_SCHOLAR_API_KEY` | unset | Optional API key. |
| `PROJECT0_CROSSREF_CONTACT_EMAIL` | unset | Optional Crossref `mailto`. |
| `PROJECT0_LOG_LEVEL` | `INFO` | Logging level. |

OpenAlex has a provider-class API-key field but no Project0 setting wired by the current factory. arXiv, OpenReview, and default OpenAlex construction are unauthenticated.

## 4. Workflow and Behavior

The agent shall:

1. Validate paired context filename and content.
2. Ingest supplied context and create structured Existing Research Context.
3. Build the deterministic strategy and bounded queries.
4. Search every configured provider for every query.
5. Consolidate duplicates, apply applicable eligibility rules, and balance the evaluation pool.
6. Normalize metadata and select an evidence shortlist of at most eight when necessary.
7. Acquire available evidence and evaluate in batches of three.
8. Sort and limit evidence-reviewed results.
9. Analyze each retained paper with usable evidence.
10. Run Direction Analysis when enabled and eligible.
11. Generate compatibility artifacts, return `ResearchResult`, and map it to the browser.

The default workflow uses evidence acquisition because the configured `PaperMetadataService` implements `acquire_evidence`.

## 5. Errors and Constraints

An individual provider/query `RuntimeError` is recorded while other groups continue. If all groups fail and return no references, the Source Service raises an aggregate failure. Partial group failures are not currently exposed in `ResearchResult.warnings` when usable results exist.

Expected `OSError`, `RuntimeError`, `TypeError`, and `ValueError` failures return `failed`. Recognized propagated HTTP 429 text produces a retry-later message. Direction Analysis failure is isolated as a warning; failures in context ingestion or analysis, strategy, query generation, sources, metadata, final evaluation, retained-paper provider calls, or artifacts fail the workflow.

All work is bounded. Scores, summaries, syntheses, and directions remain decision support and shall not be represented as exhaustive review, scientific truth, or proven novelty.

## 6. Acceptance Criteria

The specification is satisfied when valid requests produce structured traceable results or explicit warnings; invalid inputs fail safely; query and candidate bounds remain deterministic; providers remain isolated behind their protocol; duplicates preserve the richest metadata; evidence-reviewed results are correctly ordered and limited; invalid structured output cannot become unsupported findings; Direction Analysis obeys evidence-grounding rules; the browser and saved Markdown accurately represent the result; and automated unit, integration, and browser acceptance tests cover these contracts.
