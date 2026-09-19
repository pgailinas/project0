# Research Agent Testing Guide

**Version:** 1.0  
**Owner:** Project0  
**Last Updated:** 2026-09-19

## 1. Purpose and Scope

This guide supplements the repository-wide Testing Guide with Research Agent verification, environment, bounds, manual checks, and troubleshooting. Run commands from the repository root. Subset results do not establish release readiness; record exact revision, command, counts, duration, and environment.

## 2. Test Organization and Environment

Research verification covers strategy/query services; provider factory and providers; context, metadata, and evidence; evaluation and analyses; workflow/models/configuration; routes, UI mapping, integration, and browser acceptance.

Deterministic UI mode:

```bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
```

The Dashboard stub is not a reliable full-pipeline fixture: some context, paper-analysis, and direction branches are absent or schema-misaligned. Use service/integration fakes for deterministic end-to-end verification and stub Dashboard mode only for tested stages.

Live defaults are Ollama, `qwen2.5:7b`, `http://127.0.0.1:11434`, 600-second timeout, Semantic Scholar plus arXiv, and enabled Direction Analysis. Useful variables include `PROJECT0_RESEARCH_OLLAMA_MODEL`, `PROJECT0_OLLAMA_BASE_URL`, `PROJECT0_OLLAMA_TIMEOUT_SECONDS`, `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS`, and `PROJECT0_LOG_LEVEL`.

Exact source tokens are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`. Optional configuration includes `PROJECT0_SEMANTIC_SCHOLAR_API_KEY` and `PROJECT0_CROSSREF_CONTACT_EMAIL`; no Project0 variable wires the optional OpenAlex key.

## 3. Test Commands and Procedures

```bash
python -m pytest tests/unit/agents/research -v
python -m pytest tests/unit/workflow/test_research_workflow.py -v
python -m pytest tests/unit/models/test_research_models.py -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
python -m pytest
```

Focused component files use the corresponding `test_research_strategy_service.py`, `test_research_query_service.py`, source-provider/service tests, `test_research_context_ingestion_service.py`, `test_existing_research_context_analysis_service.py`, `test_paper_metadata_service.py`, `test_research_evaluation_service.py`, `test_paper_analysis_service.py`, `test_research_direction_analysis_service.py`, route/UI/view-model tests, and `test_research_agent_ui_flow.py`. Evidence acquisition belongs to `PaperMetadataService.acquire_evidence`; no separate paper-acquisition/ingestion test files exist.

Manual validation shall start the Dashboard, open `/agents/research`, confirm the Research model, submit a focused request and optional supported context, verify that submission redirects promptly to `/agents/research/runs/{run_id}`, observe backend stage and elapsed-time updates, and confirm that question, guidance, Maximum Results, and context filename remain visible in processing and terminal states. After completion, submit another request and confirm that the previous completed/error workflow styling is cleared before new progress begins. Inspect retained warnings/cards, verify evidence-backed analysis and Direction claims against papers, and inspect saved `project0_research_results.md`. The originating POST must not remain open for workflow duration.

Current bounds are 3 seeds, 3 discovery queries, up to 6 search terms, normally 10 provider results/query, 24 evaluation candidates, batches of 3, 8 evidence papers, 8,000 characters/section, 24,000 characters/paper, first 3 analyses for Direction, and 0.75 recommendation threshold. Maximum Results does not enlarge upstream bounds.

## 4. Result Interpretation

Record commit, date/environment, exact command, passed/failed/skipped totals, duration, provider/model configuration, live versus stub sources, and environmental failures. Stub output is not live-model quality evidence.

Partial provider/query failures may be logged but not returned as warnings when another group succeeds. Scored papers below 0.75 may still be displayed as reviewed but not recommended, including adjacent papers below 0.50 when result slots remain. Discovery-only and persistently unscored papers are excluded from final evidence results. Direction Analysis requires two valid analyses and may be omitted with a warning.

Explicit modern arXiv guidance seeds remain candidates when provider lookup fails: source statistics report `seed_fallback_count`, the candidate trace reports `preserved_seed`, and metadata/evidence acquisition proceeds from canonical arXiv URLs. A fallback seed can still become discovery-only when authoritative content cannot be acquired.

Canonical fallback seed titles may be enriched from usable embedded PDF metadata after evidence acquisition. Verify that the paper and nested source reference receive the same title, provider-supplied titles are preserved, and empty, generic, identifier-only, or oversized PDF titles do not replace the fallback placeholder.

Evaluation retries recover exact one-point band mistakes such as transferable 75 to 74 and adjacent 50 to 49, with a visible correction warning. Confirm that larger disagreements such as transferable 85 or direct 8 remain unscored and that every existing structural and evidence validation still applies.

## 5. Troubleshooting

- **Ollama unavailable:** Confirm service, base URL, installed Research model, and provider tests.
- **Long Direction Analysis:** The timeout is 600 seconds; disable with `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS=false` and inspect DEBUG timing/request capture.
- **No candidates:** Verify lowercase provider names, errors/rate limits, generated concepts, candidate trace, and alignment filtering.
- **Fewer than eight evidence papers:** Candidate tiers may exclude papers; abstract may survive PDF failure; no abstract/section becomes discovery-only.
- **No recommended papers:** Reviewed papers below 0.75 may remain; inspect the warning.
- **Missing paper analysis:** Evidence-free or persistently invalid analysis is skipped; a provider exception fails the workflow.
- **Missing Direction Analysis:** Confirm feature enablement, two valid analyses, and warning details.
- **Context failure:** Verify supported UTF-8/text-extractable input; OCR/chunking are unavailable and very large files may exceed model limits.
- **Save Results:** Browser save uses picker or download fallback and creates no repository artifact.
