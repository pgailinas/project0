# Research Agent Charter

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This charter defines the mission, scope, operating principles, authority
boundaries, and success criteria of the Project0 Research Agent. Detailed
runtime behavior is defined by the Research Agent Functional Specification,
Architecture, Design, and Interface Design.

---

## 2. Mission

The Research Agent helps a human researcher discover, evaluate, and analyze
technical literature. It accepts a research question, optional research
guidance, and an optional Existing Research Context document; discovers
candidate papers through configured providers; evaluates a bounded candidate
set; acquires bounded evidence for a shortlist; analyzes retained papers; and,
when sufficient analyses exist, produces evidence-grounded cross-paper
synthesis and candidate research directions.

The agent supports research judgment. It does not replace the researcher,
establish scientific truth, prove novelty, or make repository changes.

---

## 3. Goals

The current implementation is intended to:

- Convert a research request and optional prior-research document into a
  structured research strategy.
- Generate a small, deterministic set of complementary search queries.
- Search one or more configured research-source providers through a common
  provider interface.
- Balance a bounded evaluation pool across provider/query result groups while
  preserving explicit publication seeds.
- Consolidate duplicate publication records and preserve the richest available
  metadata.
- Evaluate candidates with a consistent relevance rubric.
- Acquire available abstracts and bounded PDF evidence for a shortlist.
- Preserve discovery-only status when usable paper evidence is unavailable.
- Produce evidence-cited structured analyses for retained papers.
- Produce bounded, evidence-grounded Research Direction Analysis when at least
  two valid paper analyses are available and the feature is enabled.
- Present consolidated paper cards and allow the visible result package to be
  saved as Markdown.
- Fail or warn explicitly when required inputs, provider output, evidence, or
  provenance validation is insufficient.

---

## 4. Current Scope

### Included

- Browser workflow at `/agents/research`.
- Required research question.
- Optional free-form Research Guidance.
- Maximum Results choices of 5, 10, 15, or 20 in the browser.
- Optional UTF-8 Markdown, UTF-8 plain-text, or text-extractable PDF Existing
  Research Context.
- Deterministic strategy construction and query generation.
- Explicit seed extraction from quoted titles, arXiv identifiers, and DOI
  identifiers in guidance.
- Configurable Semantic Scholar, OpenAlex, OpenReview, Crossref, arXiv, and
  stub source providers.
- Multi-provider, multi-query retrieval, provider/query-group balancing,
  deduplication, and a bounded evaluation candidate pool.
- Metadata normalization and bounded paper-evidence acquisition.
- Preliminary metadata ranking when more than eight candidates reach the
  evidence stage.
- Final evidence-based relevance evaluation.
- Structured retained-paper analysis and Research Direction Analysis.
- Consolidated results, warnings, status, system model/GPU status, and
  client-side Markdown saving.

### Excluded

- Web crawling beyond the implemented source-provider APIs and PDF URLs
  supplied by provider metadata.
- OCR for scanned or image-only PDFs.
- Vector search, embeddings, or semantic repository retrieval.
- Unbounded or exhaustive literature review.
- Independent verification of scientific claims.
- Reliable novelty or global literature-gap claims without supplied evidence.
- Automatic experimental execution.
- Automatic publication, citation-manager export, repository update, commit,
  push, or pull-request creation.
- Scheduled monitoring or multi-agent research execution.

---

## 5. Operating Principles

### Evidence first

Source metadata, acquired abstracts, bounded PDF sections, and uploaded context
are the permitted evidence for the corresponding analysis stages. Missing
information is reported or omitted; it is not invented.

### Deterministic control where practical

Input normalization, seed extraction, query bounding, provider dispatch,
deduplication, balancing, shortlist limits, result ordering, validation, and UI
mapping are deterministic. AI reasoning is used for context analysis,
relevance assessment, retained-paper analysis, and direction synthesis.

### Explicit provenance

Context findings cite the uploaded document identifier and optional section.
Paper findings cite the retained paper identifier plus a supplied evidence
section and page number when available. Direction Analysis resolves
provider-facing evidence handles back to those original references.

### Bounded work

The implementation bounds discovery queries, provider results, evaluation
batches, the evaluation pool, evidence acquisition, retained results, and
direction-analysis input. These bounds make the workflow manageable; they do
not imply complete literature coverage.

### Human authority

Scores, summaries, synthesis, and directions are decision support. The human
researcher remains responsible for interpreting evidence, checking papers, and
deciding what to pursue.

---

## 6. Authority Boundaries

The Research Agent may:

- Read a user-supplied Existing Research Context document for the current
  request.
- Query configured research providers.
- Retrieve provider-supplied open-access PDF locations.
- Invoke the configured reasoning provider.
- Return and locally save a result package through the browser.

The Research Agent may not:

- Treat generated analysis as source fact.
- Present an unsupported synthesis finding as grounded.
- Score evidence-free discovery records as evidence-reviewed results.
- Modify source papers, the uploaded context document, or the Project0
  repository.
- Commit, push, publish, or open pull requests.
- Claim comprehensive coverage, scientific correctness, or novelty.

---

## 7. Success Criteria

The implementation satisfies this charter when:

- Valid requests produce structured, traceable results or explicit warnings.
- Invalid requests and unsupported context documents fail safely.
- Search queries and candidate pools remain bounded and deterministic.
- Configured providers are isolated behind the provider protocol.
- Duplicate publications are consolidated without discarding richer metadata.
- Evidence-reviewed results are ordered by final relevance score and limited by
  Maximum Results.
- Persistent structured-output defects do not become unsupported findings.
- Direction synthesis uses validated literature evidence and candidate
  directions obey context/literature grounding rules.
- The browser accurately represents the workflow result and saved Markdown
  matches the visible consolidated package.
- Automated unit, integration, and browser acceptance tests cover the
  implementation contracts.

---

## 8. Relationship to Other Documents

- **Functional Specification** defines observable behavior.
- **Architecture** defines component organization and runtime flow.
- **Design** defines current algorithms, limits, fallback behavior, and
  configuration.
- **Interface Design** defines Python and browser contracts.
- **Testing Guide** and **Test Plan** define verification procedures and
  acceptance criteria.
- **Test Results** records repository-supported validation evidence and its
  limits.

