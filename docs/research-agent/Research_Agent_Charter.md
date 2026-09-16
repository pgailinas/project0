# Research Agent Charter

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Objectives

The Project0 Research Agent helps a human researcher discover, evaluate, and analyze technical literature. It accepts a research question, optional guidance, and optional Existing Research Context; discovers candidates through configured providers; evaluates a bounded candidate set; acquires bounded evidence; analyzes retained papers; and, when sufficient analyses exist, produces evidence-grounded cross-paper synthesis and candidate research directions.

The agent shall:

- Convert the request and optional prior-research document into a structured strategy.
- Generate a small, deterministic set of complementary queries.
- Search configured providers through a common interface and balance the bounded evaluation pool across provider/query groups while preserving explicit publication seeds.
- Consolidate duplicate publications while preserving the richest metadata.
- Evaluate candidates consistently and acquire available abstracts and bounded PDF evidence.
- Preserve discovery-only status when usable evidence is unavailable.
- Produce evidence-cited analyses and bounded Research Direction Analysis when at least two valid paper analyses exist and the feature is enabled.
- Present consolidated results and allow the visible result package to be saved as Markdown.
- Fail or warn explicitly when inputs, evidence, provenance, or provider output are insufficient.

Detailed behavior and contracts remain defined by the Research Agent Functional Specification, Architecture, Design, Interface Design, Testing Guide, Test Plan, and Test Results.

## 2. Scope and Boundaries

### Included

- Browser workflow at `/agents/research` with a required research question, optional Research Guidance, and Maximum Results of 5, 10, 15, or 20.
- Optional UTF-8 Markdown, plain-text, or text-extractable PDF Existing Research Context.
- Deterministic strategy construction, query generation, and seed extraction from quoted titles, arXiv identifiers, and DOI identifiers.
- Configurable Semantic Scholar, OpenAlex, OpenReview, Crossref, arXiv, and stub providers.
- Multi-provider, multi-query retrieval, balancing, deduplication, metadata normalization, and bounded evidence acquisition.
- Preliminary ranking, final evidence-based evaluation, retained-paper analysis, Direction Analysis, consolidated presentation, warnings, runtime status, and client-side Markdown saving.

### Excluded

- Web crawling beyond configured APIs and provider-supplied PDF locations.
- OCR, vector search, embeddings, semantic repository retrieval, or exhaustive literature review.
- Independent verification of scientific claims or reliable global novelty claims without supplied evidence.
- Automatic experiments, publication, citation-manager export, repository changes, commits, pushes, pull requests, scheduled monitoring, or multi-agent research execution.

### Authority

The agent may read the user-supplied context for the current request, query configured providers, retrieve provider-supplied open-access PDFs, invoke the configured reasoning provider, and return or locally save results through the browser.

It may not treat generated analysis as source fact, present unsupported synthesis as grounded, score evidence-free records as evidence-reviewed, modify sources or the Project0 repository, or claim comprehensive coverage, scientific correctness, or novelty.

## 3. Operating Principles

- **Evidence First:** Use source metadata, acquired abstracts, bounded PDF sections, and uploaded context as the permitted evidence for the corresponding analysis stage. Report or omit missing information rather than inventing it.
- **Deterministic Control:** Use deterministic processing for normalization, seed extraction, query bounds, dispatch, deduplication, balancing, limits, ordering, validation, and UI mapping; reserve AI reasoning for interpretive analysis.
- **Explicit Provenance:** Cite uploaded context identifiers and retained-paper evidence references, including sections and page numbers when available.
- **Bounded Work:** Bound queries, provider results, evaluation batches, candidate pools, evidence acquisition, retained results, and direction-analysis inputs without implying complete literature coverage.
- **Human Authority:** Treat scores, summaries, synthesis, and research directions as decision support. The researcher remains responsible for checking evidence and deciding what to pursue.

## 4. Success Criteria

The Research Agent is successful when:

- Valid requests produce structured, traceable results or explicit warnings, while invalid inputs fail safely.
- Queries and candidate pools remain bounded and deterministic.
- Providers remain isolated behind their common protocol.
- Duplicate publications are consolidated without loss of richer metadata.
- Evidence-reviewed results are ordered by relevance and limited by Maximum Results.
- Structured-output defects do not become unsupported findings.
- Direction synthesis uses validated evidence and obeys grounding rules.
- The browser accurately presents the workflow result and saved Markdown matches the visible package.
- Automated unit, integration, and browser acceptance tests cover the implementation contracts.

Success does not require comprehensive literature coverage, autonomous scientific judgment, or repository modification.
