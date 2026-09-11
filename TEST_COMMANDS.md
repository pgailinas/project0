# Project0 Test Commands

**Purpose:** Quick reference for repository test execution.  
**Location:** Run all commands from the project root.  
**Last Updated:** 2026-09-10

## 1. Complete Regression

~~~bash
python -m pytest
~~~

## 2. Unit Suites

~~~bash
python -m pytest tests/unit -v
python -m pytest tests/unit/agents/research -v
python -m pytest tests/unit/agents/documentation -v
~~~

### Research Agent focused unit tests

~~~bash
python -m pytest tests/unit/agents/research/test_research_strategy_service.py -v
python -m pytest tests/unit/agents/research/test_research_query_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_provider_factory.py -v
python -m pytest tests/unit/agents/research/test_semantic_scholar_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openalex_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openreview_source_provider.py -v
python -m pytest tests/unit/agents/research/test_crossref_source_provider.py -v
python -m pytest tests/unit/agents/research/test_arxiv_source_provider.py -v
python -m pytest tests/unit/agents/research/test_stub_research_source_provider.py -v
python -m pytest tests/unit/agents/research/test_research_context_ingestion_service.py -v
python -m pytest tests/unit/agents/research/test_existing_research_context_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_paper_metadata_service.py -v
python -m pytest tests/unit/agents/research/test_research_evaluation_service.py -v
python -m pytest tests/unit/agents/research/test_paper_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_research_direction_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_research_artifact_service.py -v
python -m pytest tests/unit/agents/research/test_research_agent_routes.py -v
python -m pytest tests/unit/agents/research/test_research_agent_ui_service.py -v
python -m pytest tests/unit/agents/research/test_research_agent_view_models.py -v
python -m pytest tests/unit/workflow/test_research_workflow.py -v
python -m pytest tests/unit/models/test_research_models.py -v
python -m pytest tests/unit/config/test_settings.py -v
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
python -m pytest tests/unit/dashboard/test_dashboard_app.py -v
python -m pytest tests/unit/dashboard/test_dashboard_routes.py -v
python -m pytest tests/unit/reasoning/providers/test_ollama_provider.py -v
~~~

Evidence acquisition is tested in
`tests/unit/agents/research/test_paper_metadata_service.py`. The current
repository does not contain separate
`test_research_paper_acquisition_service.py` or
`test_research_paper_ingestion_service.py` files.

## 3. Integration Suites

~~~bash
python -m pytest tests/integration -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/integration/agents/documentation -v
python -m pytest tests/integration/platform -v
~~~

### Research Agent focused integration tests

~~~bash
python -m pytest tests/integration/agents/research/test_research_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/research/test_research_agent_ui_flow.py -v
python -m pytest tests/integration/agents/research/test_research_workflow_flow.py -v
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
python -m pytest tests/integration/platform/test_ollama_reasoning_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
~~~

## 4. Acceptance Suites

~~~bash
python -m pytest tests/acceptance -v
python -m pytest tests/acceptance/agents/research -v
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/acceptance/platform -v
~~~

### Research Agent browser acceptance tests

~~~bash
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_results_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_end_to_end_acceptance.py -v
~~~

### Headed browser example

~~~bash
python -m pytest \
  tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py \
  -v -s --headed --ui-slowmo=1000
~~~

## 5. Run the Dashboard

~~~bash
python -m project0.dashboard.dashboard_app
~~~

Open `http://127.0.0.1:8001`.

### Deterministic Research Agent mode

~~~bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
~~~

### Default live mode

~~~bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=semantic_scholar,arxiv
python -m project0.dashboard.dashboard_app
~~~

See `docs/agents/research/Research_Agent_Testing_Guide.md` for current
configuration, expected bounds, live-provider caveats, and troubleshooting.

