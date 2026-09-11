# Research Agent Testing Guide

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This guide explains how to verify and troubleshoot the implemented Project0
Research Agent. Run commands from the repository root in the Project0 Python
environment.

---

## 2. Fast Verification

### Research Agent unit tests

~~~bash
python -m pytest tests/unit/agents/research -v
~~~

### Workflow and configuration tests

~~~bash
python -m pytest \
  tests/unit/workflow/test_research_workflow.py \
  tests/unit/models/test_research_models.py \
  tests/unit/config/test_settings.py \
  tests/unit/platform/test_platform_dispatcher.py \
  tests/unit/dashboard/test_dashboard_app.py \
  tests/unit/dashboard/test_dashboard_routes.py \
  -v
~~~

### Research integration tests

~~~bash
python -m pytest tests/integration/agents/research -v
~~~

### Research browser acceptance

~~~bash
python -m pytest tests/acceptance/agents/research -v
~~~

### Complete regression

~~~bash
python -m pytest
~~~

Do not report a passing Research Agent release from a subset alone. Record the
exact command, revision, pass/fail/skip totals, duration, and environment.

---

## 3. Focused Test Commands

### Strategy and query generation

~~~bash
python -m pytest tests/unit/agents/research/test_research_strategy_service.py -v
python -m pytest tests/unit/agents/research/test_research_query_service.py -v
~~~

### Source service, factory, and providers

~~~bash
python -m pytest tests/unit/agents/research/test_research_source_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_provider_factory.py -v
python -m pytest tests/unit/agents/research/test_semantic_scholar_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openalex_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openreview_source_provider.py -v
python -m pytest tests/unit/agents/research/test_crossref_source_provider.py -v
python -m pytest tests/unit/agents/research/test_arxiv_source_provider.py -v
python -m pytest tests/unit/agents/research/test_stub_research_source_provider.py -v
~~~

### Context, metadata, and evidence

~~~bash
python -m pytest tests/unit/agents/research/test_research_context_ingestion_service.py -v
python -m pytest tests/unit/agents/research/test_existing_research_context_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_paper_metadata_service.py -v
~~~

Evidence acquisition is implemented by `PaperMetadataService.acquire_evidence`;
there are no separate current test files named
`test_research_paper_acquisition_service.py` or
`test_research_paper_ingestion_service.py`.

### Evaluation and analysis

~~~bash
python -m pytest tests/unit/agents/research/test_research_evaluation_service.py -v
python -m pytest tests/unit/agents/research/test_paper_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_research_direction_analysis_service.py -v
python -m pytest tests/unit/workflow/test_research_workflow.py -v
~~~

### Routes and presentation

~~~bash
python -m pytest tests/unit/agents/research/test_research_agent_routes.py -v
python -m pytest tests/unit/agents/research/test_research_agent_ui_service.py -v
python -m pytest tests/unit/agents/research/test_research_agent_view_models.py -v
python -m pytest tests/integration/agents/research/test_research_agent_ui_flow.py -v
~~~

---

## 4. Deterministic Dashboard Mode

For local UI work that must avoid external research APIs and Ollama, configure:

~~~bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
~~~

Then open:

~~~text
http://127.0.0.1:8001/agents/research
~~~

The stub path exists for deterministic development/testing, but it is not a
currently reliable full-pipeline fixture. The evaluation branch is covered by
the Dashboard unit tests. The Dashboard stub's Existing Research Context,
paper-analysis, and direction-analysis branches are absent or use fields and
evidence identifiers that do not match the current service schemas. Use the
service and integration test fakes for deterministic end-to-end verification;
use Dashboard stub mode only for the stages exercised by its tests until those
fixtures are brought back into alignment. Stub output must never be treated as
a live-model quality test.

---

## 5. Live Ollama Configuration

Default live configuration:

~~~bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=semantic_scholar,arxiv
python -m project0.dashboard.dashboard_app
~~~

Defaults apply when the variables are omitted:

- provider: `ollama`;
- Research model: `qwen2.5:7b`;
- base URL: `http://127.0.0.1:11434`;
- timeout: 600 seconds; and
- Direction Analysis: enabled.

Useful overrides:

~~~bash
export PROJECT0_RESEARCH_OLLAMA_MODEL=qwen2.5:7b
export PROJECT0_OLLAMA_BASE_URL=http://127.0.0.1:11434
export PROJECT0_OLLAMA_TIMEOUT_SECONDS=600
export PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS=true
export PROJECT0_LOG_LEVEL=DEBUG
~~~

`PROJECT0_RESEARCH_OLLAMA_MODEL` falls back to
`PROJECT0_OLLAMA_MODEL`, then `qwen2.5:7b`. Supported reasoning-provider
configuration in the Dashboard composition is `ollama` or `stub`.

The current local engineering selection is `qwen2.5:7b` for the Research
Agent. This is a Project0 configuration decision, not a universal model-quality
claim.

---

## 6. Research Provider Configuration

Select a comma-separated list using exact lowercase names:

~~~bash
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=openalex,crossref,arxiv
~~~

Supported names:

~~~text
semantic_scholar
openalex
openreview
crossref
arxiv
stub
~~~

Optional provider configuration:

~~~bash
export PROJECT0_SEMANTIC_SCHOLAR_API_KEY=<key>
export PROJECT0_CROSSREF_CONTACT_EMAIL=<email>
~~~

There is no Project0 environment variable wired to OpenAlex's optional
provider-class API-key field. OpenReview and arXiv are used without
authentication.

With multiple providers, each provider receives each generated query. A
partial provider/query runtime failure is tolerated when another group returns
results. Such partial failures appear in logs but are not currently returned as
workflow warnings.

---

## 7. Manual Functional Check

1. Start the Dashboard.
2. Open `/agents/research`.
3. Confirm the system panel shows the Research Agent model.
4. Submit a specific question and optional guidance.
5. Optionally upload a small UTF-8 Markdown/text file or text-extractable PDF.
6. Confirm the submitted values remain visible.
7. Review workflow warnings before interpreting the result cards.
8. Confirm every card has one source identity, metadata, relevance assessment,
   and structured analysis only when supported.
9. If Direction Analysis appears, verify claims against the underlying papers;
   evidence validation does not replace human review.
10. Select **Save Results** and inspect
    `project0_research_results.md`.

The visible progress control is client-side. A long-running request does not
stream individual server workflow stages.

---

## 8. Expected Bounds

| Boundary | Current value |
| --- | ---: |
| Explicit seeds | 3 |
| Discovery queries | 3 |
| Total current search terms | up to 6 |
| Provider results per query | normally 10 |
| Balanced evaluation pool | 24 |
| Preliminary/final evaluation batch | 3 |
| Evidence shortlist | 8 |
| Extracted evidence per section | 8,000 characters |
| Extracted evidence total per paper | 24,000 characters |
| Direction Analysis papers | first 3 valid analyses |
| Recommendation threshold | 0.75 |

Maximum Results limits the final displayed set; it does not increase the
24-candidate or eight-paper upstream bounds.

---

## 9. Troubleshooting

### “Ollama service could not be reached”

- Confirm Ollama is running.
- Confirm `PROJECT0_OLLAMA_BASE_URL`.
- Confirm the configured Research model is installed.
- Run the Ollama provider unit/integration tests.

### Long Research Direction Analysis

- The default timeout is 600 seconds.
- Set `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS=false` to isolate earlier
  stages.
- Use DEBUG logging to inspect stage timing and the direction request capture
  at `/tmp/project0_direction_analysis_request.json`.

The boolean parser enables only `1`, `true`, `yes`, and `on`
case-insensitively. Other values, including `false`, disable the feature.

### No candidates

- Confirm `PROJECT0_RESEARCH_SOURCE_PROVIDERS` contains supported lowercase
  names.
- Inspect source-provider errors and rate limits.
- At DEBUG level, inspect generated strategy concepts, candidate trace, and
  `outside_alignment_profile` selections.
- Remember that the current alignment profile can filter candidates for
  visual-language alignment-shaped strategies.

### Fewer than eight evidence papers

- Preliminary Evidence Candidate tiers can exclude tier-2 candidates.
- PDF retrieval failure can still retain an abstract.
- A paper with neither abstract nor extracted PDF section becomes
  discovery-only and is excluded from final evidence results.

### No recommended papers

Evidence-reviewed papers below 0.75 can still be displayed. The workflow emits
a warning and the UI distinguishes reviewed results from recommended results.

### Missing paper analysis

- Evidence-free discovery-only papers are skipped.
- Persistent structural/provenance failure skips the individual analysis.
- A provider exception in Paper Analysis fails the overall workflow.

### Missing Research Direction Analysis

- At least two valid paper analyses are required.
- The feature may be disabled.
- A validation/provider failure is isolated as a workflow warning and the
  Direction Analysis is omitted.

### Existing Research Context failure

- Confirm the extension and UTF-8/text-extractable content.
- OCR is not available.
- Context is not chunked; very large documents can exceed practical model
  limits.
- Context analysis structured-output defects receive only one retry.

### Save Results behavior

Saving occurs in the browser. Where `showSaveFilePicker` is unavailable or
cancelled, the code uses a download fallback. No server-side file or repository
artifact is created by the button.

---

## 10. Recording Results

Record:

- full commit SHA;
- date and environment;
- exact command;
- passed, failed, and skipped totals;
- duration;
- provider/model configuration;
- whether external APIs or stub providers were used; and
- any expected skips or environmental failures.

Do not copy historical counts into a new Test Results entry without executing
the stated command against the stated revision.
