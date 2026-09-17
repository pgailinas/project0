# Research Agent Test Plan

**Version:** 0.9  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

This plan defines verification of the implemented Research Agent across deterministic unit, assembled integration, browser acceptance, live-provider, and repository regression boundaries. It covers requests/context, strategy/query bounds, all configured providers, balancing/deduplication, metadata/evidence, evaluation, paper and Direction Analysis, UI/save behavior, configuration, safety, and failure handling.

Live Ollama and research APIs provide environment-dependent evidence and do not replace deterministic regression. The Dashboard's built-in Research stub is not a complete integration oracle because later analysis fixtures are not fully aligned with current schemas.

## 2. Verification Strategy

- **Unit:** Isolate provider parsing, deterministic services, workflow decisions, models, UI mapping, routes, settings, and reasoning-provider behavior.
- **Integration:** Assemble production components with controlled external boundaries and verify handoffs, consolidation, upload forwarding, rendering, and dispatcher behavior.
- **Browser acceptance:** Exercise the local Dashboard form, processing state, consolidated results, unsupported-information safeguards, and end-to-end outcomes through Playwright.
- **Live checks:** Evaluate Ollama and configured APIs separately, recording environmental failures, rate limits, rankings, and model variability independently from deterministic counts.
- **Regression:** Run the complete Project0 suite so Research changes do not break shared platform or other-agent behavior.

Repository content and tests are authoritative. Missing evidence must remain absent or explicitly warned; model output, inventory, and historical results do not establish current correctness.

## 3. Test Coverage and Scenarios

### Requests and context

Verify route registration, ready state, normalization and multiline preservation, blank-question rejection without execution, paired filename/bytes, supported Markdown/text/PDF ingestion, safe failure for invalid or non-extractable content, provenance, exactly three distinct solution concepts, preservation of model anchors, and one retry for invalid structured output.

### Strategy, queries, and providers

Verify ordered concepts/constraints/sub-questions, seed extraction and ordering, context-inferred solution concepts, exclusion of existing-project findings and conclusions from search concepts, objective deduplication, at most three complementary discovery dimensions, overlap removal, eight-word compaction, role diversity, deterministic empty input, and all six provider-factory entries.

Provider scenarios shall cover request construction, parsing, credentials, retries/failures, independent provider/query dispatch, Crossref omission for arXiv-only queries, multi-provider aggregation, partial and aggregate failure, 24-candidate bound, round-robin balance, query-anchor priority, seed preservation, DOI/arXiv/title-author-year identity, richest-version merge, trace reasons, alignment-profile inclusion/exclusion, and rejection of generic teacher/representation lexical matches without a complete visual-language alignment mechanism.

### Metadata, evidence, and evaluation

Verify provider normalization, Semantic Scholar fallback, abstract evidence, PDF/type validation, page-preserving section extraction, eight-paper and 24,000-character limits, discovery-only state, preliminary ranking, three-paper batches, opaque IDs, integer 0–100 normalization, high-score transfer checks, partial recovery plus one retry, persistent unscored defects, threshold-independent evidence retention, score ordering, and Maximum Results.

### Paper and Direction Analysis

Verify evidence-limited prompts, exact section/page citations, abstract versus full-paper basis, discovery-only skip, one structural retry and per-paper skip, Direction minimum two and maximum three papers, literature grounding, two-paper support for themes/comparisons/shared limitations, one-paper unresolved questions, direction context/literature requirements, handle type/uniqueness/count, speculative anchors, performance-order rejection, omission of ordinary invalid synthesis items, and full retry for semantic or candidate-direction failure.

### UI, save, and safety

Verify consolidated cards, one title URL, recommended versus reviewed counts, warning/error states, context filename in form and analysis, Direction display, hidden legacy artifacts, completion-gated **Save Results**, and saved filename/content.

A test must fail if the agent executes a blank question; accepts unsupported context; invents metadata/evidence; confuses source IDs with model handles; accepts unknown/wrong-type evidence; presents unsupported performance comparisons or ungrounded non-speculative directions; scores evidence-free records as final evidence results; exceeds documented bounds; or writes to the Project0 repository.

Primary coverage resides under `tests/unit/agents/research/`, `tests/unit/workflow/test_research_workflow.py`, Research models/configuration/dispatcher/Dashboard/reasoning tests, `tests/integration/agents/research/`, relevant platform integration, and `tests/acceptance/agents/research/`. Evidence acquisition belongs to `test_paper_metadata_service.py`; no separate acquisition or ingestion service test files exist.

## 4. Environment and Test Data

Deterministic tests shall use contract-correct stubs/fakes, controlled provider responses, supported context fixtures, malformed and provenance-invalid structured output, duplicate/identity cases, and explicit expected bounds. Browser acceptance requires a separately running Dashboard and Playwright. Live checks require configured Ollama/model and external-provider access.

Execution groups are:

```bash
python -m pytest tests/unit/agents/research tests/unit/workflow/test_research_workflow.py tests/unit/models/test_research_models.py tests/unit/config/test_settings.py -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
python -m pytest
```

## 5. Entry and Exit Criteria

Entry requires an identified commit, installed dependencies for selected levels, deterministic fixtures, browser prerequisites when applicable, and documented live-provider configuration.

Exit requires that every command names current files; deterministic unit/integration suites pass; applicable browser acceptance passes; the complete Project0 regression passes; skips and environmental exclusions are understood; and Test Results records the exact command, revision, date, environment, outcomes, and limitations.

## 6. Known Gaps

- Built-in Dashboard stubs do not fully represent current context, paper-analysis, and Direction schemas.
- Live providers and models remain variable and cannot establish deterministic regression.
- Evidence acquisition is covered within `PaperMetadataService`, not a separately named acquisition service.
- This plan records required coverage, not a current aggregate pass count.
