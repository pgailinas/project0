# Project0 Test Commands

**Purpose:** Quick reference for repository verification.  
**Location:** Run every command from the Project0 repository root.  
**Last Updated:** 2026-09-19

For testing principles, ownership boundaries, environment details, naming, result interpretation, and test-development guidance, see `docs/platform/Testing_Guide.md`.

## 1. Install Declared Test Dependencies

```bash
python -m pip install -e '.[test]'
```

The declared test extra installs pytest and httpx in addition to Project0's runtime dependencies.

Browser acceptance tests additionally import Playwright and require its pytest fixtures and browser binaries. Those browser dependencies are not declared in `pyproject.toml` at the pinned commit and must be provisioned separately.

## 2. Complete Pytest Collection

```bash
python -m pytest
```

This command collects applicable tests under `tests/unit/`, `tests/integration/`, and `tests/acceptance/`. Browser modules can fail to collect or run if their external Playwright environment is absent, and UI tests require a separately running Dashboard at `http://127.0.0.1:8001`.

## 3. Test Layers

```bash
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/acceptance -v
```

## 4. Reusable Platform Suites

### Unit directories

```bash
python -m pytest tests/unit/artifacts -v
python -m pytest tests/unit/common -v
python -m pytest tests/unit/config -v
python -m pytest tests/unit/dashboard -v
python -m pytest tests/unit/knowledge -v
python -m pytest tests/unit/models -v
python -m pytest tests/unit/platform -v
python -m pytest tests/unit/reasoning -v
python -m pytest tests/unit/repository -v
python -m pytest tests/unit/skills -v
python -m pytest tests/unit/validation -v
```

### Generic workflow and shared review coordination

```bash
python -m pytest tests/unit/workflow/test_workflow_engine.py -v
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
```

`test_documentation_workflow.py` and `test_research_workflow.py` reside in `tests/unit/workflow/` but verify agent-specific workflow coordinators.

### Platform integration

```bash
python -m pytest tests/integration/platform -v
```

Focused platform integration files:

```bash
python -m pytest tests/integration/platform/test_core_platform_flow.py -v
python -m pytest tests/integration/platform/test_context_builder_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
python -m pytest tests/integration/platform/test_knowledge_service_flow.py -v
python -m pytest tests/integration/platform/test_reasoning_service_flow.py -v
python -m pytest tests/integration/platform/test_ollama_reasoning_flow.py -v
python -m pytest tests/integration/platform/test_validation_service_flow.py -v
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
```

## 5. Documentation Agent Suites

```bash
python -m pytest tests/unit/agents/documentation -v
python -m pytest tests/integration/agents/documentation -v
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/unit/workflow/test_documentation_workflow.py -v
python -m pytest tests/unit/models/test_documentation_workflow_models.py -v
```

Focused integration files:

```bash
python -m pytest tests/integration/agents/documentation/test_documentation_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_agent_ui_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_workflow_flow.py -v
```

See `docs/documentation-agent/Documentation_Agent_Testing_Guide.md` for scenario ownership, acceptance requirements, provider configuration, and troubleshooting.

## 6. Research Agent Suites

```bash
python -m pytest tests/unit/agents/research -v
python -m pytest tests/integration/agents/research -v
python -m pytest tests/acceptance/agents/research -v
python -m pytest tests/unit/workflow/test_research_workflow.py -v
python -m pytest tests/unit/models/test_research_models.py -v
```

### Focused Research service units

```bash
python -m pytest tests/unit/agents/research/test_research_strategy_service.py -v
python -m pytest tests/unit/agents/research/test_research_query_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_provider_factory.py -v
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
```

### Focused Research source-provider units

```bash
python -m pytest tests/unit/agents/research/test_research_source_provider.py -v
python -m pytest tests/unit/agents/research/test_semantic_scholar_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openalex_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openreview_source_provider.py -v
python -m pytest tests/unit/agents/research/test_crossref_source_provider.py -v
python -m pytest tests/unit/agents/research/test_arxiv_source_provider.py -v
python -m pytest tests/unit/agents/research/test_stub_research_source_provider.py -v
python -m pytest tests/unit/reasoning/providers/test_ollama_provider.py -v
```

Research-paper evidence acquisition is implemented and tested in `tests/unit/agents/research/test_paper_metadata_service.py`. The repository does not contain separate `test_research_paper_acquisition_service.py` or `test_research_paper_ingestion_service.py` files.

### Focused Research integration

```bash
python -m pytest tests/integration/agents/research/test_research_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/research/test_research_agent_ui_flow.py -v
python -m pytest tests/integration/agents/research/test_research_workflow_flow.py -v
```

See `docs/research-agent/Research_Agent_Testing_Guide.md` for provider bounds, live/stub configuration, manual checks, and troubleshooting.

## 7. Browser Acceptance

Use deterministic providers for the normal browser regression path.

Terminal 1:

```bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
```

Terminal 2:

```bash
python -m pytest tests/acceptance/agents/documentation -v
python -m pytest tests/acceptance/agents/research -v
```

The acceptance suite does not start the Dashboard. Use the executable module above so both agent interfaces are registered.

### Headed browser example

```bash
python -m pytest \
  tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py \
  -v -s --headed --ui-slowmo=1000
```

`--ui-slowmo=<milliseconds>` is registered by `tests/acceptance/conftest.py`, defaults to zero, and rejects negative values. It is an observation aid, not a synchronization mechanism.

## 8. Explicit Per-File Commands

All per-file test commands in addition to the broader directory-level suites above.

```bash
python -m pytest tests/unit/artifacts/test_artifact_location_service.py -v
python -m pytest tests/unit/artifacts/test_markdown_locator.py -v
python -m pytest tests/unit/common/test_logging_config.py -v
python -m pytest tests/unit/common/test_startup_validation.py -v
python -m pytest tests/unit/config/test_settings.py -v
python -m pytest tests/unit/dashboard/test_dashboard_app.py -v
python -m pytest tests/unit/dashboard/test_dashboard_routes.py -v
python -m pytest tests/unit/knowledge/test_context_builder.py -v
python -m pytest tests/unit/knowledge/test_context_filters.py -v
python -m pytest tests/unit/knowledge/test_context_formatter.py -v
python -m pytest tests/unit/knowledge/test_context_rules.py -v
python -m pytest tests/unit/knowledge/test_document_index.py -v
python -m pytest tests/unit/knowledge/test_document_parser.py -v
python -m pytest tests/unit/knowledge/test_document_selector.py -v
python -m pytest tests/unit/knowledge/test_knowledge_service.py -v
python -m pytest tests/unit/models/test_artifact_models.py -v
python -m pytest tests/unit/models/test_context_models.py -v
python -m pytest tests/unit/models/test_knowledge_models.py -v
python -m pytest tests/unit/models/test_reasoning_models.py -v
python -m pytest tests/unit/models/test_validation_models.py -v
python -m pytest tests/unit/models/test_workflow_models.py -v
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
python -m pytest tests/unit/reasoning/test_prompt_builder.py -v
python -m pytest tests/unit/reasoning/test_reasoning_service.py -v
python -m pytest tests/unit/reasoning/providers/test_stub_provider.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
python -m pytest tests/unit/repository/test_repository_service.py -v
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/validation/test_documentation_consistency_validator.py -v
python -m pytest tests/unit/validation/test_link_validator.py -v
python -m pytest tests/unit/validation/test_markdown_validator.py -v
python -m pytest tests/unit/validation/test_mkdocs_validator.py -v
python -m pytest tests/unit/validation/test_validation_service.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_routes.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_ui_service.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_view_models.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_approval_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_request_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_review_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_results_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_end_to_end_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_request_acceptance.py -v -s --headed --ui-slowmo=1000
```

## 9. Frequently Used Pytest Options

```bash
python -m pytest -v
python -m pytest -x
python -m pytest --durations=10
python -m pytest path/to/test_file.py -v
python -m pytest path/to/test_file.py::test_name -v
```

Use `-s` to display captured output. Browser-specific options such as `--headed` require the externally provisioned Playwright pytest integration.

## 10. Non-Pytest Integrity Checks

```bash
python -m compileall -q src
mkdocs build --strict
```

At pinned commit `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`, `compileall` failed because `src/project0/interfaces/knowledge_interfaces.py` contained Markdown fence lines. The fences were subsequently removed, and compilation of `src` and `tests` passed in the local checkout at `70cf6f7` on 2026-09-19. Rerun the command above for the revision being validated.

## 11. Run Applications for Manual or Browser Validation

Command-line startup workflow:

```bash
python -m project0.main
```

Dashboard with default live reasoning configuration:

```bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=semantic_scholar,arxiv
python -m project0.dashboard.dashboard_app
```

Documentation server:

```bash
mkdocs serve
```

The Dashboard uses `http://127.0.0.1:8001`. MkDocs normally uses `http://127.0.0.1:8000` and must be started separately.

## 12. Result Reporting

A pass count is current only when the relevant command ran against an identified source state in a suitable environment. Record the commit, command, date, environment, provider mode, pass/fail/error/skip counts, excluded live checks, and separate compilation/documentation-build outcomes.

Do not treat an empty test file, collected test, skipped test, stub-provider test, historical count, or unexecuted command as current passing evidence.

At the pinned audit commit, pytest and MkDocs were unavailable, so no current pytest or strict MkDocs result was established. The earlier `1265 passed, 11 skipped` record from 2026-09-09 was not tied to the pinned commit and remains historical only.
