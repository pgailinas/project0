# Research Agent Design

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Executive Summary

The Research Agent combines deterministic request parsing, bounded multi-query retrieval, provider balancing, metadata/evidence acquisition, and presentation with schema-constrained reasoning for context analysis, relevance evaluation, paper analysis, and research-direction synthesis. The design preserves explicit evidence provenance, isolates retryable generated-output defects, and limits search, evidence, evaluation, and synthesis work. Several candidate-selection rules remain specialized for visual/video-language representation research and are not domain-independent.

## 2. Purpose and Scope

This document records the current detailed Research Agent design. It describes implemented component behavior, interactions, configuration, failure handling, and constraints rather than future intentions. Public field declarations and browser contracts belong in the Interface Design; executable requirements belong in the Functional Specification.

`create_project0_dashboard_app()` assembles the Research dispatcher with strategy, query, source, metadata, evaluation, artifact, context-ingestion, context-analysis, paper-analysis, and direction-analysis services. Selected source names and the Research model are supplied to the relevant services.

## 3. Component Design

### Request and context

The POST route accepts `question`, `guidance`, integer `max_results` defaulting to 10, and optional `context_document`. The UI trims text, retains the normalized filename, and forwards bytes without storage.

Markdown/text are decoded as UTF-8. PDF page text is extracted with pypdf and joined with two newlines; page boundaries are not retained in `extracted_text`. `ResearchContextDocument` records UUID, filename, type, extraction method, status, and PDF page count. The service performs no OCR or chunking.

Context reasoning returns an optional research problem; prior work, approaches, findings, limitations, unresolved questions, and future work; and solution-search concepts. Findings receive the upload UUID and optional section provenance. With a question, exactly three source/target/mechanism concepts with distinct mechanisms are required. Acronym and encoder/decoder anchors from the question are restored when absent. Retryable structural or field errors receive one retry; provider exceptions do not.

### Strategy and queries

Strategy construction is deterministic. Ordered concepts combine programmatic focus, guidance, question, and context-inferred solution-search concepts, removing exact duplicates. Existing-project findings, limitations, unresolved questions, stated future work, and research-problem prose remain context evidence and do not become literature-search concepts. Constraints include programmatic values and guidance beginning `prefer`, `focus`, `avoid`, or `require`; question-form guidance becomes sub-questions. The first three unique quoted titles, arXiv IDs, or DOI IDs become seeds.

The Query Service normalizes seeds, derives compact context queries and direct/mechanism/transfer/application dimensions, removes exact and high-overlap candidates, selects at most three discovery queries, removes queries with at least 60% term-stem overlap with a seed, and returns seeds first. Discovery candidates overlap substantially at 75% of the smaller meaningful-term set. At most three seeds plus three normally eight-word discovery queries produce six search terms.

### Providers and retrieval

Provider names are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`; the default is `semantic_scholar,arxiv`. Names are case-sensitive and unsupported names fail construction. External providers retry transient errors, HTTP 429, and server failures up to three attempts using provider-specific delay behavior.

The Source Service calls each provider for each query, skipping Crossref for arXiv-only input. Duplicate identity uses provider/source ID, normalized DOI/arXiv ID, or normalized title with compatible year and overlapping authors. Canonical richness considers abstract length, author count, metadata count, year, and URL; missing fields are merged.

The alignment profile activates when strategy terms collectively contain visual, language, and mechanism vocabulary. Seeds bypass exclusion. Non-seed candidates must provide either a direct video-language representation-alignment path or a transferable visual-language representation-alignment mechanism; generic lexical matches without that complete path are excluded. Hard-coded visual/video-language rules also influence evidence tiers and are not general domain-independent ranking. Within provider/query groups, deterministic overlap ranking precedes round-robin selection to the default 24-candidate pool.

### Metadata, evidence, and evaluation

All providers map to `PaperMetadata`; only Semantic Scholar receives a separate detail request. When more than eight papers exist, preliminary scoring and direct/transferable visual-language tiers choose at most eight eligible candidates. With eight or fewer, all proceed without that tier filter.

Evidence acquisition adds abstracts, follows authoritative PDF metadata or derived arXiv PDF URLs, validates PDF content, and extracts recognized Abstract, Method/Methodology/Approach/Model, and Experiment/Results/Evaluation sections. Each section is limited to 8,000 characters and total evidence to 24,000, preserving heading page and removing duplicates. No evidence produces `discovery_only`; such papers are counted and then removed from displayed final results.

Evaluation batches contain at most three papers identified as batch-local `paper-NNN`. The schema requires score, summary, strengths, limitations, connections, and warnings. Scores use the documented 0–100 relevance rubric, require an explicit transfer connection at 50+, and receive contradiction checks at 75+. When deterministic evidence changes a mechanism band, the corrected connection replaces stale generated connections and limitations that negate the corrected direct or transferable mapping are removed; unrelated limitations remain. Integer scores normalize to 0.0–1.0; invalid identity/coverage/high-score entries are partially recovered and retried once. Persistent unresolved records remain unscored and are excluded from final results. Final evidence results retain scored, evidence-bearing papers in descending score order up to `max(1, max_results)`, allowing adjacent evidence below 0.50 to fill otherwise unused result slots.

### Paper and direction analysis

One request analyzes each retained paper. Required problem and approach plus optional findings are bound to that paper; every finding cites supplied evidence and exact page when present. Missing structure or invalid fields retry once, then skip the paper; provider exceptions propagate.

Direction Analysis runs with at least two valid analyses and uses the first three. Deterministic context/literature handles enforce known, unique provenance. Themes, comparisons, and shared limitations require two papers; unresolved questions require one. Performance comparisons require matching evidence polarity. Non-speculative directions require literature and, when present, context evidence; speculative directions require at least one anchor. Ordinary invalid synthesis items are omitted, while semantic or direction-structure errors retry the full response once and then become an isolated workflow warning.

### Presentation and diagnostics

The UI joins sources, papers, evaluations, and analyses by source ID into consolidated cards. Evaluation warnings become deduplicated relevance limitations. Legacy Literature Comparison, Research Gap Analysis, and Experiment Proposal artifacts remain unrendered compatibility outputs. Browser **Save Results** separately builds `project0_research_results.md` from the visible package using File System Access or Blob download.

INFO logs aggregate selection counts; DEBUG logs candidate traces. The system-status panel polls `/api/system-status?agent=research` every two seconds during submission and reports provider/model and NVIDIA GPU data, not workflow-stage telemetry. Direction Analysis may write its Ollama payload to `/tmp/project0_direction_analysis_request.json`.

## 4. Interactions and Contracts

The Platform Dispatcher owns composition and passes the Research model to all reasoning services. Services depend on `ReasoningProviderProtocol`, not Ollama. Principal immutable contracts cover requests, strategy, source references, metadata, evidence, context, evaluations, paper analyses, synthesis/directions, artifacts, and `ResearchResult`; source providers implement `ResearchSourceProviderProtocol`.

Execution flows from optional context ingestion through strategy/query generation, nested provider retrieval, deduplication and balancing, metadata normalization, optional preliminary ranking, evidence acquisition, final evaluation, retained-paper analysis, optional Direction Analysis, compatibility artifacts, and browser mapping.

## 5. Configuration and Failure Behavior

| Setting | Default |
| --- | --- |
| Reasoning provider | `ollama` |
| Research model | `qwen2.5:7b` |
| Ollama URL | `http://127.0.0.1:11434` |
| Ollama timeout | 600 seconds |
| Source providers | `semantic_scholar`, `arxiv` |
| Evaluation pool | 24 |
| Evidence shortlist | 8 |
| Evaluation batch | 3 |
| Direction input | first 3 analyses |
| Direction Analysis | enabled |
| Recommendation threshold | 0.75 |

The workflow constructor obtains the direction-analysis flag from module-level `SETTINGS`; normal environment startup honors the override, but a custom `ProjectSettings` passed only to `create_platform_dispatcher` does not override that constructor default.

No source results, incomplete metadata, discovery-only candidates, no recommended papers, and isolated Direction failure produce `completed_with_warnings`. Recoverable structured-output defects follow the retries above. Provider exceptions propagate except where the workflow explicitly isolates Direction Analysis or the source service has another successful group.

## 6. Constraints and Verification

- Context is one reasoning request with no chunk limit or page provenance.
- PDF extraction is heading/page-dependent rather than a complete parser.
- Candidate profile and evidence tiers contain domain-specific vocabulary.
- Partial source/query failures are not surfaced when another group succeeds.
- OpenAlex's optional API key is not wired through `ProjectSettings`.
- Custom dispatcher settings do not directly override the workflow constructor's direction flag.
- Legacy artifacts differ from the browser-saved package.
- Model reasoning remains variable despite schemas, deterministic checks, and retries.

Verification shall cover deterministic bounds, provider construction and dispatch, identity and recovery rules, evidence grounding, UI consolidation, configuration, warning/failure behavior, and the distinction between current capability and future design.
