# Research Agent Functional Specification

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This document defines the implemented inputs, processing behavior, outputs,
configuration, and failure handling of the Project0 Research Agent.

---

## 2. Inputs

### Research question

The browser and Platform Dispatcher require a non-empty research question.
Whitespace is trimmed by the UI service. A blank browser submission returns a
failed page without starting the workflow.

### Research guidance

Research Guidance is optional free-form text. Deterministic strategy parsing:

- splits guidance on line breaks and sentence-ending periods without breaking
  decimal identifiers;
- treats items beginning with `prefer`, `focus`, `avoid`, or `require` as
  constraints;
- treats items ending in `?` as sub-questions;
- uses remaining non-empty items as ordered concepts; and
- extracts up to three explicit publication seeds from quoted titles, arXiv
  identifiers, and DOI identifiers.

The form does not provide separate source, constraint, or focus-area controls.
Those fields exist in the Python `ResearchRequest` model for programmatic use.

### Maximum Results

The browser offers 5, 10, 15, and 20; the default is 10. The workflow uses
`max(1, max_results)` when slicing final results. The Platform Dispatcher does
not otherwise validate an arbitrary programmatic value.

### Existing Research Context

An optional upload may be:

- `.md` or `.markdown` containing UTF-8 text;
- `.txt` containing UTF-8 text; or
- `.pdf` with extractable text.

The filename and bytes must be supplied together. Empty files, unsupported
extensions, invalid UTF-8, malformed PDFs, and PDFs without extractable text
fail the workflow. OCR and document chunking are not implemented. The extracted
text is sent as one reasoning request.

---

## 3. Functional Workflow

1. Validate paired context filename/content inputs.
2. If context is supplied, ingest it and create structured Existing Research
   Context.
3. Build a deterministic Research Strategy.
4. Generate bounded provider-ready queries.
5. Search every configured provider for each generated query.
6. Consolidate duplicates, apply the implemented eligibility profile when
   triggered, and balance the evaluation pool.
7. Normalize metadata.
8. If more than eight candidates remain, perform preliminary metadata ranking
   and select an evidence shortlist of at most eight.
9. Acquire available abstract and PDF evidence for the shortlist.
10. Perform final evidence-based evaluation in batches of three.
11. Order and limit evidence-reviewed results.
12. Produce structured analysis for each retained paper that has usable
    evidence.
13. When enabled and at least two valid paper analyses exist, perform Research
    Direction Analysis using at most the first three analyses.
14. Generate three legacy in-memory compatibility artifacts when evaluations
    exist.
15. Return a `ResearchResult` and map it to the browser view.

The default workflow uses the evidence-acquisition path because the configured
`PaperMetadataService` implements `acquire_evidence`.

---

## 4. Strategy and Query Generation

### Strategy

The strategy preserves:

- objective;
- ordered concepts;
- up to three seed terms;
- sub-questions;
- constraints;
- configured source names;
- rationale; and
- inferred solution-search concepts from Existing Research Context.

When both the request objective and request-derived concepts are empty, the
strategy contains no executable sources or queries.

Context analysis must return exactly three inferred solution-search concepts
when a research question is supplied. Each concept contains a source
representation/model, target model/space, and distinct mechanism. Explicit
model/encoder/decoder anchors found in the question are restored when omitted
from generated concepts.

### Query bounds

The Query Service:

- preserves exact seed queries first;
- creates at most three discovery queries;
- produces no more than six total search terms because the Strategy Service
  emits at most three seeds;
- normally limits generated discovery queries to eight words;
- removes exact duplicates and substantially overlapping query dimensions; and
- selects complementary roles in direct, mechanism, transfer, and application
  order where those roles can be derived.

Query generation is deterministic and provider-independent.

---

## 5. Source Retrieval

### Supported and default providers

Supported configuration names are:

- `semantic_scholar`
- `openalex`
- `openreview`
- `crossref`
- `arxiv`
- `stub`

The default configured providers are `semantic_scholar,arxiv`. Merely being
supported does not make a provider active.

### Dispatch and failure handling

Each configured provider is called once for each search term, in configured
provider order and query order. Crossref is skipped for a query that consists
only of an arXiv identifier or arXiv URL.

An individual provider/query `RuntimeError` is recorded internally and other
groups continue. If all attempted groups fail and no references are returned,
the Source Service raises an aggregated failure. If any references are
returned, successful results continue; individual group failures are not
currently exposed in `ResearchResult.warnings`.

### Deduplication and balancing

Duplicates match by:

- identical provider name and source identifier;
- shared normalized DOI or arXiv identifier; or
- normalized title with compatible publication year and overlapping authors
  when both author sets are present.

The richest duplicate becomes canonical, and missing complementary metadata is
merged. Explicit seed matches are preserved first. Remaining results are
ranked within each provider/query group by deterministic term overlap, then
selected round-robin across groups until the default 24-candidate evaluation
limit is reached.

For strategies that contain visual, language, and alignment-mechanism anchors,
the current Source Service applies an alignment-oriented eligibility profile.
It retains direct video-language alignment candidates, transferable
visual-language candidates, preserved seeds, and candidates that do not expose
contradictory profile terms. It can exclude clearly unrelated modalities/tasks
and, for representation-learning strategies, synthesis/generation candidates.
This is current heuristic behavior, not a general relevance guarantee.

Search statistics record retrieved, deduplicated, preserved-seed, and selected
evaluation-candidate counts. A detailed candidate trace is logged at DEBUG.

---

## 6. Metadata and Evidence

Metadata is normalized for Semantic Scholar, arXiv, OpenAlex, OpenReview,
Crossref, and stub references. Semantic Scholar performs a detail request and
falls back to search-result metadata after exhausted HTTP failures. The other
providers use their normalized search-result metadata.

For at most eight shortlisted papers, evidence acquisition:

- includes the available abstract as an `Abstract` evidence section;
- follows an authoritative `open_access_pdf_url` or `pdf_url` supplied in
  metadata;
- derives an arXiv PDF URL from an arXiv abstract URL;
- verifies that a retrieved response is a PDF;
- extracts text following recognizable Abstract, Method/Methodology/Approach/
  Model, and Experiment/Results/Evaluation headings;
- limits an extracted section to 8,000 characters and all acquired evidence to
  24,000 characters; and
- preserves the page on which each extracted section heading occurs.

PDF retrieval/extraction failure falls back to any available abstract. A paper
with no usable abstract or extracted section is marked `discovery_only`.

---

## 7. Relevance Evaluation and Selection

Evaluation requests contain at most three papers. Provider-facing paper IDs are
opaque batch-local values (`paper-001`, `paper-002`, and so on), not external
source IDs.

The provider returns an integer score from 0 through 100 or null; the service
normalizes it to 0.0 through 1.0. A score of 0.75 is the recommendation
threshold. Final high scores must not contradict the required
mechanism-to-question transfer path. A discovery-only paper without content is
not sent for final model scoring and receives an unscored record.

If output omits, duplicates, corrupts, or invents an expected batch identifier,
or produces a contradictory high score, the service preserves valid partial
evaluations and retries unresolved papers once. Persistent unresolved papers
receive unscored invalid-response evaluations. Non-retryable type/schema errors
and provider failures propagate to the workflow.

In the default evidence path, final selection:

- excludes papers with no evidence sections;
- sorts remaining evaluations by descending final score, with null last;
- retains at most Maximum Results; and
- does not discard evidence-reviewed papers solely for scoring below 0.75.

Consequently, the UI can display reviewed papers below the recommendation
threshold and issues a warning when none is recommended. The legacy
no-evidence-acquisition selection path filters to scores of at least 0.75.

---

## 8. Retained-Paper Analysis

Each retained paper is analyzed separately using only its supplied evidence
sections and metadata. Required output includes a problem and approach;
optional arrays cover representations, modalities, learning/alignment
objectives, datasets/tasks, findings, limitations, and warnings.

Every finding must cite a supplied evidence section and the supplied page
number when present. Abstract evidence uses a null page. The service retries a
missing or structurally invalid response once. A persistent structural failure
skips that paper's analysis; a provider exception propagates and fails the
workflow.

The analysis basis is `paper_content` if any evidence section has a page number;
otherwise it is `abstract_metadata`.

---

## 9. Research Direction Analysis

Research Direction Analysis is enabled by default and runs only when its service
is configured and at least two valid paper analyses exist. It receives at most
the first three analyses.

The service:

- exposes deterministic opaque evidence handles to the model;
- restricts synthesis to literature evidence;
- requires themes, comparisons, and shared limitations to cite at least two
  distinct papers;
- permits unresolved questions with evidence from at least one paper;
- rejects explicit performance-ordering claims unless the same polarity is
  directly stated by cited literature findings;
- requires a non-speculative direction to cite literature evidence and, when
  context exists, context evidence;
- permits speculative directions only when explicitly marked and anchored to
  context or literature evidence; and
- resolves accepted handles back to original context/paper provenance.

Ordinary invalid synthesis items are logged and omitted individually. Semantic
performance-grounding errors and invalid candidate-direction structures cause
one complete retry. If the retry still fails, the workflow completes with a
warning and omits Direction Analysis.

---

## 10. Outputs and UI

`ResearchResult` contains status, summary, strategy, all selected source
references, retained papers/evaluations, in-memory artifacts, optional Existing
Research Context, paper analyses, optional Direction Analysis, warnings, and
source/evidence-review statistics.

The browser presents:

- workflow status and warnings;
- request values and the uploaded context filename;
- Existing Research Context findings;
- one consolidated card per retained paper with source details, abstract,
  relevance assessment, and available structured analysis;
- Research Direction Analysis when returned; and
- source/paper/evaluation counts.

Legacy `ResearchArtifactService` output is retained in the result model but is
not rendered. The **Save Results** button creates
`project0_research_results.md` in the browser from the visible consolidated
request, context, papers, assessments, analyses, and directions.

---

## 11. Status and Errors

Successful execution returns `completed` or `completed_with_warnings`. Expected
`OSError`, `RuntimeError`, `TypeError`, and `ValueError` failures return a
`failed` result. Source HTTP 429 errors receive a user-oriented retry-later
message when the propagated message contains the recognized status text.

Direction Analysis failure is isolated as a warning. Context ingestion,
context analysis, strategy, query, source, metadata, final evaluation,
retained-paper provider failure, and artifact failures fail the workflow.

---

## 12. Runtime Configuration

| Environment variable | Default | Behavior |
| --- | --- | --- |
| `PROJECT0_REASONING_PROVIDER` | `ollama` | Dashboard composition accepts `ollama` or `stub`. |
| `PROJECT0_RESEARCH_SOURCE_PROVIDERS` | `semantic_scholar,arxiv` | Comma-separated, case-sensitive provider names. |
| `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS` | `True` | False-like values disable; only `1`, `true`, `yes`, and `on` enable. |
| `PROJECT0_RESEARCH_OLLAMA_MODEL` | `PROJECT0_OLLAMA_MODEL` or `qwen2.5:7b` | Research Agent model. |
| `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` | Shared model fallback. |
| `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API base URL. |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | `600.0` | Default request timeout; Direction Analysis also requests 600 seconds. |
| `PROJECT0_SEMANTIC_SCHOLAR_API_KEY` | unset | Optional Semantic Scholar API key. |
| `PROJECT0_CROSSREF_CONTACT_EMAIL` | unset | Optional Crossref `mailto` parameter. |
| `PROJECT0_LOG_LEVEL` | `INFO` | Project0 logging level. |

OpenAlex has an optional provider-class API-key field, but no corresponding
Project0 setting is wired by the current factory. arXiv, OpenReview, and the
default OpenAlex construction are unauthenticated.

