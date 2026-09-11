# Research Agent Design

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This document records the current detailed design of the Research Agent. It is
descriptive of the implementation at the documented revision; it does not
define unimplemented intentions.

---

## 2. Composition

`create_project0_dashboard_app()` creates a Research Agent dispatcher with:

- `ResearchStrategyService`;
- `ResearchQueryService`;
- `ResearchSourceService` and configured providers;
- `PaperMetadataService`;
- `ResearchEvaluationService`;
- `ResearchArtifactService`;
- `ResearchContextIngestionService`;
- `ExistingResearchContextAnalysisService`;
- `PaperAnalysisService`; and
- `ResearchDirectionAnalysisService`.

The dispatcher passes the selected provider names into both Strategy Service
and Provider Factory. It passes the Research Agent model name to every
reasoning-backed research service.

The `ResearchWorkflow` constructor defaults its direction-analysis flag from
the module-level `SETTINGS.research_direction_analysis_enabled`. The dispatcher
does not explicitly forward a custom `ProjectSettings` value for this flag.
Normal application startup imports `SETTINGS` from the environment, so the
documented environment override applies; isolated callers supplying a different
settings object to `create_platform_dispatcher` do not currently override this
constructor default.

---

## 3. Request and Context Design

### Browser request

The POST route accepts:

| Form field | Type | Default |
| --- | --- | --- |
| `question` | text | empty; rejected by UI |
| `guidance` | text | empty |
| `max_results` | integer | 10 |
| `context_document` | optional upload | none |

The UI trims question/guidance and retains the normalized filename for display.
It forwards file bytes without storing a copy.

### Context ingestion

Markdown and text are decoded as UTF-8 without rewriting their content. PDF
pages are read with pypdf; non-empty extracted page strings are joined with two
newlines. The resulting `ResearchContextDocument` includes a UUID, source
filename, type, extraction method, status, and PDF page count where applicable.

The service does not preserve page boundaries in `extracted_text` and does not
chunk the document. Context findings can cite a recognizable section string,
but page-number provenance is not requested or stored for context findings.

### Context structured output

The provider must return:

- optional `research_problem`;
- arrays for prior work, implemented approaches, findings, limitations,
  unresolved questions, and stated future work; and
- `inferred_solution_search_concepts`.

Each ordinary finding requires non-empty content and a string-or-null section.
The service attaches the uploaded document UUID to every finding.

When a research question is supplied, exactly three solution concepts are
required. Each item has non-empty source, target, and mechanism fields; all
three mechanisms must differ. Fields are combined with duplicate words removed.
Question tokens that look like acronyms or include `encoder`/`decoder` become
required anchors and are prepended when absent. Retryable structured-output or
field errors receive one retry; provider exceptions are not retried here.

---

## 4. Strategy Design

The Strategy Service is deterministic.

### Ordered concepts

Concepts are appended in this order:

1. explicit `focus_areas` from programmatic requests;
2. non-constraint, non-question guidance items;
3. the normalized question concept;
4. context-inferred solution concepts;
5. context unresolved questions;
6. context stated future work;
7. context limitations;
8. context findings; and
9. the context research problem.

Implemented approaches and prior work from context are not directly appended as
strategy concepts. Exact duplicate strings are removed while preserving first
occurrence.

### Constraints and sub-questions

Programmatic constraints are followed by guidance items beginning with
`prefer`, `focus`, `avoid`, or `require`. Guidance constraints receive a trailing
period. Guidance items ending in a question mark become sub-questions.

### Seeds

The first three unique quoted titles, arXiv identifiers, or DOI identifiers in
guidance become `seed_terms`. Quoted text is treated as a seed even if it is not
actually a publication title.

---

## 5. Query Design

The Query Service does not call a model or provider.

### Construction

1. Normalize and deduplicate seeds.
2. Build compact queries from inferred context solution concepts.
3. Convert strategy concepts and `Focus on ...` constraints into candidate
   dimensions.
4. Detect directive guidance and research roles.
5. When suitable, derive distinct direct, mechanism, transfer, and application
   role queries.
6. Remove exact and high-overlap candidates.
7. Select at most three discovery queries.
8. Remove discovery queries with 60% or greater term-stem overlap with a seed.
9. Return seeds followed by discovery queries.

Substantial overlap among discovery candidates is defined as at least 75%
relative to the smaller meaningful-term set.

### Bounds

- Strategy Service: at most three seeds.
- Query Service: at most three discovery dimensions.
- Generated discovery query: normally at most eight words.
- Total current search terms: at most six.

Seeds are preserved as entered after whitespace normalization and are not
subject to the eight-word discovery-query limit.

---

## 6. Provider and Retrieval Design

### Configuration

The supported names are `semantic_scholar`, `openalex`, `openreview`,
`crossref`, `arxiv`, and `stub`. Names are selected from a comma-separated
environment value without case normalization. Unsupported names fail provider
construction.

Default selection is:

~~~text
semantic_scholar,arxiv
~~~

### Provider behavior

| Provider | Endpoint family | Per-call result bound | Notable behavior |
| --- | --- | ---: | --- |
| Semantic Scholar | Graph API paper search/detail | 10 | Optional API key; search retries; detail fallback to search metadata. |
| OpenAlex | `/works` | 10 | Provider class supports an API key, but application settings do not wire one. |
| OpenReview | API2 `/notes/search` | 10 retained | Requests up to 50 notes, then keeps submission-like forum notes and filters reviews/DBLP records. |
| Crossref | `/works` | 10 | Optional contact `mailto`; invalid individual items are skipped. |
| arXiv | public Atom API | 10 | 60-second default timeout; returns normalized Atom entries. |
| stub | in-memory | configured tuple | Records strategies and can raise a configured error. |

External providers use up to three attempts for transient request errors,
HTTP 429, and server failures. They honor numeric `Retry-After` where
implemented and otherwise use exponential delays. Exact error messages and
delay caps differ by provider.

### Dispatch

The Source Service converts each search term into a one-term strategy and calls
providers in this nested order:

~~~text
for provider in configured providers:
    for query in strategy.search_terms:
        provider.search(one-query strategy)
~~~

Crossref is not called for a one-term query that is only an arXiv identifier or
arXiv URL.

### Duplicate identity

Two references are duplicates when they share provider/source ID, a normalized
DOI/arXiv identifier, or a normalized title with compatible year and authors.
Title matching ignores accents, case, and punctuation. When both records have
authors, at least one normalized author must overlap.

Canonical richness is ordered by abstract length, author count, metadata-field
count, presence of year, then presence of URL. Missing/blank metadata fields
from the alternate record are merged into the canonical record.

### Eligibility profile

The Source Service enables its alignment profile when strategy concepts and
queries collectively contain visual, language, and mechanism terms. Direct and
transferable candidates are identified from title plus abstract tokens.
Explicit seeds bypass profile exclusion. Candidates with no profile vocabulary
can remain, while candidates exposing incompatible language/task or
representation-synthesis vocabulary can be excluded.

This profile and the Evidence Candidate tiers in `ResearchWorkflow` contain
hard-coded visual/video-language representation-learning vocabulary. They are
not dynamically derived from arbitrary research domains.

### Balanced pool

Within each provider/query group, candidates are sorted by a tuple of:

1. title overlap with terms repeated across strategy queries;
2. title/abstract overlap with repeated anchor terms;
3. title overlap with that group's query; and
4. title/abstract overlap with that query.

Seeds enter first. The selector then takes one candidate from each group per
round, skipping duplicates, until the default `evaluation_candidate_limit` of
24 is reached. Candidate statistics and trace records are diagnostic state,
not fields on the strategy.

---

## 7. Metadata and Evidence Design

### Metadata normalization

All supported provider names map to `PaperMetadata`. Missing optional fields
remain null/empty. Semantic Scholar is the only provider for which the metadata
service makes a separate detail request.

### Shortlist

The workflow-level evidence candidate limit is eight. If metadata contains
more than eight papers:

1. `rank_candidates` performs preliminary metadata evaluation;
2. Evidence Candidate tiers put direct video-language-representation transfer
   candidates before transferable visual-language candidates;
3. unrelated or excluded candidates receive tier 2 and are not eligible;
4. scores order candidates within a tier; and
5. at most eight eligible papers proceed.

If eight or fewer papers exist, all proceed directly to evidence acquisition;
the workflow-specific tier filter is not applied at that point.

### Evidence acquisition

For each shortlisted paper:

- add a non-empty abstract as `ResearchPaperEvidenceSection("Abstract", ...)`;
- inspect paper and source-reference metadata for
  `open_access_pdf_url`/`pdf_url`;
- for arXiv, convert an `/abs/` URL to `/pdf/`;
- retrieve and validate PDF content;
- extract Abstract, Method/Methodology/Approach/Model, and
  Experiment/Results/Evaluation sections only when a matching heading occurs
  on a page; and
- take at most 8,000 characters after each heading and 24,000 characters total.

Evidence records preserve the heading page, not a complete page range.
Duplicate evidence sections are removed. Any non-empty evidence yields
`available`; otherwise status is `discovery_only`.

The workflow's `discovery_only_count` counts papers with no evidence sections.
Its warning is added before final selection. The final default evidence path
then removes those papers from displayed results.

---

## 8. Evaluation Design

### Batch identity and schema

Batches contain at most three papers. External source IDs are replaced with
`paper-NNN` handles scoped to the batch. The schema requires exactly one item
per paper with score, summary, strengths, limitations, connections, and
warnings.

### Relevance rubric

The provider prompt defines:

- 90–100: direct application/task and central-problem alignment;
- 75–89: a major technical dimension plus application alignment or a concrete
  supported transfer path;
- 50–74: related mechanism with an incomplete transfer path;
- 25–49: background/adjacent work without a specific mapping; and
- 0–24: weakly related or off-topic.

Scores of at least 50 require an explicit mechanism-to-question connection.
Scores of at least 75 receive additional contradiction checks. The returned
integer is divided by 100; integer-valued floats are accepted, but booleans,
fractional scores, and out-of-range values are rejected.

### Recovery

On retryable identity, coverage, or high-score defects:

- valid items are retained;
- unknown/duplicate/invalid items are ignored for partial recovery;
- only unresolved papers are retried once; and
- persistent unresolved papers receive a null score and explicit warnings.

Other malformed field types and provider exceptions propagate.

### Final result selection

The default evidence path keeps evaluations whose papers have evidence
sections, sorts descending by score with null last, and takes
`max(1, max_results)`. It does not apply the 0.75 threshold as an exclusion.
Recommendation is a presentation property derived from `score >= 0.75`.

---

## 9. Paper Analysis Design

One provider request is made per retained paper. Abstract evidence is added to
the evidence-section list if the paper has an abstract and no explicit
`Abstract` section.

The response does not return paper IDs. Required `problem` and `approach` and
all optional findings are bound to the paper already being processed. Each
finding must cite a supplied section and exact page number when one exists.
When abstract evidence exists and the model supplies both section and page as
null, the service normalizes the citation to `Abstract`.

Missing structured output and provider-field validation errors are retried
once. Persistent structural failure skips the paper. Provider exceptions
propagate. A discovery-only paper without abstract content is skipped without a
provider call.

---

## 10. Research Direction Analysis Design

### Input

Direction Analysis runs for at least two valid analyses and truncates input to
the first three. Context and paper findings are cataloged with deterministic
internal paths, then exposed to the provider as sequential
`context-NNN`/`literature-NNN` handles.

### Output rules

The schema requires synthesis arrays and candidate directions.

- Themes, comparisons, and shared limitations require cited evidence from at
  least two distinct papers.
- Unresolved questions require at least one paper.
- Evidence lists must contain known, unique handles of the expected source
  type and may not exceed the distinct literature-source count.
- Explicit better/worse/higher/lower/outperform/underperform-style comparisons
  are accepted only when cited literature findings contain matching
  performance polarity.
- Non-speculative directions always require literature evidence and also
  context evidence when context exists.
- A speculative direction requires at least one evidence anchor.

Ordinary invalid synthesis findings are caught, logged, and omitted. The
performance-comparison guard raises a semantic grounding error that invalidates
the response. Invalid candidate directions also invalidate the response. The
whole request is retried once with the first validation error included as
feedback. A second failure propagates to the workflow, which converts it to a
warning and omits Direction Analysis.

---

## 11. Artifact and Presentation Design

### In-memory artifacts

When evaluations exist, `ResearchArtifactService` returns:

- Literature Comparison;
- Research Gap Analysis; and
- Experiment Proposal.

They are deterministic compatibility artifacts, omit source references, and
are counted in the workflow summary string. The current page model does not
carry them, and template artifact markup is disabled with `{% if false %}`.

### Consolidated cards

The UI joins papers, evaluations, source references, and paper analyses by
source ID. Each displayed card includes one title link at most, source details,
abstract/fallback text, relevance fields, and optional structured analysis.
Evaluation warnings are deduplicated into the displayed Relevance Limitations;
the card-level warning tuple is cleared.

### Saved Markdown

On a completed page, **Save Results** builds
`project0_research_results.md` in JavaScript. It includes the request, optional
context filename and findings, consolidated paper results, available analyses,
Direction Analysis, and a generation timestamp. The browser uses the File
System Access API when available and otherwise downloads a Blob.

This saved file is not a server-side `ResearchArtifact` and is not written to
the repository.

---

## 12. Status, Logging, and Diagnostics

`completed_with_warnings` is returned for:

- no source references;
- incomplete metadata count;
- discovery-only evidence-shortlist members;
- no recommended evidence-reviewed papers; or
- isolated Direction Analysis failure.

The source service logs aggregate selection counts at INFO and candidate traces
at DEBUG. Direction Analysis may write its Ollama request payload to
`/tmp/project0_direction_analysis_request.json` through request metadata.

The browser system-status panel polls `/api/system-status?agent=research` every
two seconds during a submitted request. It reports configured provider/model
and NVIDIA GPU information; it is operational status, not true workflow-stage
telemetry.

---

## 13. Configuration

| Setting | Default |
| --- | --- |
| Reasoning provider | `ollama` |
| Research model | `qwen2.5:7b` |
| Ollama base URL | `http://127.0.0.1:11434` |
| Ollama timeout | 600 seconds |
| Active source providers | `semantic_scholar`, `arxiv` |
| Evaluation candidate pool | 24 |
| Evidence shortlist | 8 |
| Evaluation batch | 3 |
| Direction input | first 3 paper analyses |
| Direction Analysis | enabled |
| Recommendation threshold | 0.75 |

Environment-variable names and fallback rules are listed in the Functional
Specification and Testing Guide.

---

## 14. Known Implementation Constraints

- Context is sent in one reasoning request; there is no chunk limit.
- PDF section extraction is heading- and page-dependent and is not a complete
  paper parser.
- The current candidate profile and evidence tiers include domain-specific
  visual/video-language terminology.
- Partial source-query failures are not surfaced when another group succeeds.
- The optional OpenAlex provider API key is not configurable through
  `ProjectSettings`.
- A caller-supplied `ProjectSettings.research_direction_analysis_enabled` is
  not explicitly forwarded by the dispatcher; normal environment-based global
  settings remain effective.
- Legacy artifacts are not the browser-saved result package.

