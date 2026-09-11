# Research Agent Test Plan

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Purpose

This plan defines verification of the implemented Project0 Research Agent
across unit, integration, browser acceptance, live-provider, and regression
boundaries.

---

## 2. Objectives

Testing shall establish that:

- request and upload interfaces fail safely;
- strategies and queries are deterministic and bounded;
- every supported source provider normalizes its external response;
- provider/query dispatch, balancing, deduplication, and candidate tracing
  preserve required identity and order;
- metadata and evidence fallbacks do not invent content;
- evaluation and analysis structured output is validated and recovered only
  through documented retry rules;
- unsupported synthesis findings are omitted or cause Direction Analysis to be
  withheld;
- the default configuration and environment overrides are honored;
- consolidated UI cards and saved-result controls match workflow data; and
- Research Agent changes do not regress the broader Project0 suite.

---

## 3. Test Levels

### Unit

Unit tests isolate provider parsing, service algorithms, workflow decisions,
model properties, UI mapping, route delegation, settings, and reasoning
provider behavior.

### Integration

Integration tests assemble real Project0 components with deterministic fakes or
stubs. They verify service handoffs, provider-version consolidation, request
upload forwarding, consolidated result rendering, and dispatcher integration.
The Dashboard's built-in reasoning stub is not itself the integration oracle:
only its evaluation identifier behavior is directly covered, and its later
analysis fixtures are not aligned with the current schemas.

### Browser acceptance

Playwright tests exercise the local Dashboard through the rendered Research
Agent interface. They verify the request form, processing state, visible source
metadata/evaluation/artifact-equivalent results, unsupported-information
safety, and end-to-end outcomes.

### Live external/provider checks

Ollama and external research APIs are environment-dependent. Live checks
complement deterministic tests but are not a substitute for them. A provider
failure, rate limit, changed ranking, or model wording can be environmental
rather than a deterministic regression.

---

## 4. Authoritative Test Inventory

### Research Agent unit tests

~~~text
tests/unit/agents/research/test_arxiv_source_provider.py
tests/unit/agents/research/test_crossref_source_provider.py
tests/unit/agents/research/test_existing_research_context_analysis_service.py
tests/unit/agents/research/test_openalex_source_provider.py
tests/unit/agents/research/test_openreview_source_provider.py
tests/unit/agents/research/test_paper_analysis_service.py
tests/unit/agents/research/test_paper_metadata_service.py
tests/unit/agents/research/test_research_agent_routes.py
tests/unit/agents/research/test_research_agent_ui_service.py
tests/unit/agents/research/test_research_agent_view_models.py
tests/unit/agents/research/test_research_artifact_service.py
tests/unit/agents/research/test_research_context_ingestion_service.py
tests/unit/agents/research/test_research_direction_analysis_service.py
tests/unit/agents/research/test_research_evaluation_service.py
tests/unit/agents/research/test_research_query_service.py
tests/unit/agents/research/test_research_source_provider.py
tests/unit/agents/research/test_research_source_provider_factory.py
tests/unit/agents/research/test_research_source_service.py
tests/unit/agents/research/test_research_strategy_service.py
tests/unit/agents/research/test_semantic_scholar_source_provider.py
tests/unit/agents/research/test_stub_research_source_provider.py
~~~

Cross-cutting unit coverage includes:

~~~text
tests/unit/config/test_settings.py
tests/unit/dashboard/test_dashboard_app.py
tests/unit/dashboard/test_dashboard_routes.py
tests/unit/models/test_research_models.py
tests/unit/platform/test_platform_dispatcher.py
tests/unit/reasoning/providers/test_ollama_provider.py
tests/unit/reasoning/test_prompt_builder.py
tests/unit/reasoning/test_reasoning_service.py
tests/unit/workflow/test_research_workflow.py
~~~

### Integration tests

~~~text
tests/integration/agents/research/test_research_agent_end_to_end_flow.py
tests/integration/agents/research/test_research_agent_ui_flow.py
tests/integration/agents/research/test_research_workflow_flow.py
tests/integration/platform/test_dashboard_flow.py
tests/integration/platform/test_ollama_reasoning_flow.py
tests/integration/platform/test_platform_dispatcher_flow.py
~~~

### Browser acceptance tests

~~~text
tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py
tests/acceptance/agents/research/test_research_agent_ui_results_acceptance.py
tests/acceptance/agents/research/test_research_agent_ui_end_to_end_acceptance.py
~~~

There are no files named
`test_research_paper_acquisition_service.py` or
`test_research_paper_ingestion_service.py` in the current repository.
Evidence acquisition is covered by `test_paper_metadata_service.py`.

---

## 5. Functional Coverage

### Request and context

Verify:

- ready page and route registration;
- form-value normalization and multiline preservation;
- blank-question rejection without workflow execution;
- filename/byte forwarding;
- Markdown, text, and PDF ingestion;
- invalid/empty/unsupported/scanned-style input failure;
- context provenance;
- exactly three distinct inferred solution concepts for a supplied question;
- explicit model-anchor preservation; and
- one validation retry followed by failure on persistent invalid output.

Primary tests:

~~~text
test_research_agent_routes.py
test_research_agent_ui_service.py
test_research_context_ingestion_service.py
test_existing_research_context_analysis_service.py
test_research_agent_ui_flow.py
~~~

### Strategy and bounded multi-query generation

Verify:

- ordered concept/constraint/sub-question extraction;
- seed extraction and seed-first ordering;
- preservation of context-derived solution concepts;
- exclusion of the objective duplicate;
- at most three complementary discovery dimensions;
- overlap removal;
- eight-word compaction for generated dimensions;
- distinct role selection; and
- deterministic empty-input behavior.

Primary tests:

~~~text
test_research_strategy_service.py
test_research_query_service.py
test_research_workflow.py
~~~

### Providers, balancing, and deduplication

Verify:

- all six provider factory entries;
- provider request construction, parsing, optional credentials, retry, and
  failure behavior;
- independent provider/query dispatch;
- Crossref omission for arXiv-only queries;
- multi-provider aggregation;
- continued operation after partial runtime failure;
- aggregate failure when all groups fail;
- 24-candidate bound;
- group-balanced selection and query-anchor priority;
- seed preservation;
- DOI/arXiv/title-author-year duplicate matching;
- richest-version choice and complementary metadata merge;
- candidate trace selection reasons; and
- alignment-profile inclusion/exclusion behavior.

Primary tests:

~~~text
test_*_source_provider.py
test_research_source_provider_factory.py
test_research_source_service.py
test_research_workflow_flow.py
~~~

### Metadata, evidence, evaluation, and retained selection

Verify:

- provider-specific metadata normalization;
- Semantic Scholar detail fallback;
- abstract evidence;
- PDF validation and page-preserving section extraction;
- 8-paper and 24,000-character bounds;
- discovery-only classification;
- preliminary ranking before evidence acquisition;
- evaluation batches of three;
- opaque ID validation;
- 0–100 integer score normalization;
- high-score transfer-path guard;
- partial retention and one retry for unresolved evaluations;
- unscored persistent retryable defects;
- evidence-path retention across recommendation thresholds; and
- final score ordering and Maximum Results.

Primary tests:

~~~text
test_paper_metadata_service.py
test_research_evaluation_service.py
test_research_workflow.py
test_research_workflow_flow.py
~~~

### Paper and Direction Analysis

Verify:

- evidence-limited paper prompts;
- exact section/page provenance;
- abstract/full-paper analysis basis;
- discovery-only skip;
- one paper-analysis retry and per-paper skip after persistent structural
  failure;
- Direction Analysis minimum/two-paper and maximum/three-paper bounds;
- literature-only synthesis grounding;
- two-paper support for themes/comparisons/shared limitations;
- single-paper support for unresolved questions;
- candidate context/literature requirements;
- evidence-handle type, uniqueness, and count validation;
- speculative evidence anchoring;
- unsupported performance-ordering rejection;
- individual omission of ordinary invalid synthesis items; and
- full retry for invalid candidate or semantic grounding errors.

Primary tests:

~~~text
test_paper_analysis_service.py
test_research_direction_analysis_service.py
test_research_workflow.py
~~~

### UI and save behavior

Verify:

- consolidated source/paper/evaluation/analysis card;
- one visible title URL per paper;
- recommended versus reviewed counts;
- page warning/error status;
- Existing Research Context filename in the form and analysis;
- Direction Analysis display;
- hidden legacy artifact panel;
- **Save Results** availability after completion; and
- saved Markdown content/filename behavior through browser tests where
  practical.

Primary tests:

~~~text
test_research_agent_view_models.py
test_research_agent_ui_service.py
test_research_agent_ui_flow.py
test_research_agent_ui_*_acceptance.py
~~~

---

## 6. Safety and Failure Criteria

A test must fail if the implementation:

- starts a workflow for a blank browser question;
- silently accepts unsupported context input;
- invents paper metadata or evidence;
- confuses external source IDs with batch-local model handles;
- accepts unknown or wrong-type evidence handles;
- presents an unsupported performance comparison as grounded;
- presents a non-speculative direction without its required evidence;
- scores evidence-free discovery records as final evidence-based results;
- exceeds documented query/evaluation/evidence/direction bounds; or
- writes to the Project0 repository from the Research Agent workflow.

---

## 7. Execution

~~~bash
python -m pytest tests/unit/agents/research tests/unit/workflow/test_research_workflow.py tests/unit/models/test_research_models.py tests/unit/config/test_settings.py -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
python -m pytest
~~~

Browser acceptance requires the repository's Playwright test setup. Live
Ollama validation additionally requires the configured service/model.

---

## 8. Completion Criteria

Documentation synchronization is complete only when:

- every command names files present in the repository;
- deterministic Research Agent unit and integration suites pass;
- applicable browser acceptance tests pass;
- the complete Project0 regression suite passes;
- any skipped tests are understood and recorded;
- environment-dependent checks are labeled separately; and
- the Test Results document records the exact command, revision, date, result,
  and limitations of an actual run.
