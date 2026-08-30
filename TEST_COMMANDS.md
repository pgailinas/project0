Project0 Test Commands

Purpose:
Quick reference for running Project0 validation tests.

Location:
Run all commands from project root.

Last Updated:
2026-08-27


1) UNIT TEST COMMANDS:
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
python -m pytest tests/unit/models/test_documentation_workflow_models.py -v
python -m pytest tests/unit/models/test_knowledge_models.py -v
python -m pytest tests/unit/models/test_reasoning_models.py -v
python -m pytest tests/unit/models/test_research_models.py -v
python -m pytest tests/unit/models/test_validation_models.py -v
python -m pytest tests/unit/models/test_workflow_models.py -v
python -m pytest tests/unit/platform/test_platform_dispatcher.py -v
python -m pytest tests/unit/reasoning/test_prompt_builder.py -v
python -m pytest tests/unit/reasoning/test_reasoning_service.py -v
python -m pytest tests/unit/reasoning/providers/test_ollama_provider.py -v
python -m pytest tests/unit/reasoning/providers/test_stub_provider.py -v
python -m pytest tests/unit/repository/test_git_diff_service.py -v
python -m pytest tests/unit/repository/test_repository_service.py -v
python -m pytest tests/unit/repository/test_repository_update_service.py -v
python -m pytest tests/unit/validation/test_documentation_consistency_validator.py -v
python -m pytest tests/unit/validation/test_link_validator.py -v
python -m pytest tests/unit/validation/test_markdown_validator.py -v
python -m pytest tests/unit/validation/test_mkdocs_validator.py -v
python -m pytest tests/unit/validation/test_validation_service.py -v
python -m pytest tests/unit/workflow/test_documentation_workflow.py -v
python -m pytest tests/unit/workflow/test_research_workflow.py -v
python -m pytest tests/unit/workflow/test_review_coordinator.py -v
python -m pytest tests/unit/workflow/test_workflow_engine.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_routes.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_ui_service.py -v
python -m pytest tests/unit/agents/documentation/test_documentation_agent_view_models.py -v
python -m pytest tests/unit/agents/research/test_arxiv_source_provider.py -v
python -m pytest tests/unit/agents/research/test_paper_metadata_service.py -v
python -m pytest tests/unit/agents/research/test_research_agent_routes.py -v
python -m pytest tests/unit/agents/research/test_research_agent_ui_service.py -v
python -m pytest tests/unit/agents/research/test_research_agent_view_models.py -v
python -m pytest tests/unit/agents/research/test_research_artifact_service.py -v
python -m pytest tests/unit/agents/research/test_research_evaluation_service.py -v
python -m pytest tests/unit/agents/research/test_research_query_service.py -v
python -m pytest tests/unit/agents/research/test_research_source_provider.py -v
python -m pytest tests/unit/agents/research/test_research_source_provider_factory.py -v
python -m pytest tests/unit/agents/research/test_research_source_service.py -v
python -m pytest tests/unit/agents/research/test_research_strategy_service.py -v
python -m pytest tests/unit/agents/research/test_semantic_scholar_source_provider.py -v
python -m pytest tests/unit/agents/research/test_stub_research_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openalex_source_provider.py -v
python -m pytest tests/unit/agents/research/test_crossref_source_provider.py -v
python -m pytest tests/unit/agents/research/test_openreview_source_provider.py -v
python -m pytest tests/unit/agents/research/test_research_context_ingestion_service.py -v
python -m pytest tests/unit/agents/research/test_existing_research_context_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_research_paper_acquisition_service.py -v
python -m pytest tests/unit/agents/research/test_research_paper_ingestion_service.py -v
python -m pytest tests/unit/agents/research/test_paper_analysis_service.py -v
python -m pytest tests/unit/agents/research/test_research_direction_analysis_service.py -v


2) FULL UNIT TEST SUITE:
python -m pytest tests/unit -v

3) INTEGRATION TEST COMMANDS:
python -m pytest tests/integration/platform/test_core_platform_flow.py -v
python -m pytest tests/integration/platform/test_context_builder_flow.py -v
python -m pytest tests/integration/platform/test_dashboard_flow.py -v
python -m pytest tests/integration/platform/test_knowledge_service_flow.py -v
python -m pytest tests/integration/platform/test_ollama_reasoning_flow.py -v
python -m pytest tests/integration/platform/test_platform_dispatcher_flow.py -v
python -m pytest tests/integration/platform/test_reasoning_service_flow.py -v
python -m pytest tests/integration/platform/test_validation_service_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_agent_ui_flow.py -v
python -m pytest tests/integration/agents/documentation/test_documentation_workflow_flow.py -v
python -m pytest tests/integration/agents/research/test_research_agent_end_to_end_flow.py -v
python -m pytest tests/integration/agents/research/test_research_agent_ui_flow.py -v
python -m pytest tests/integration/agents/research/test_research_workflow_flow.py -v

4) FULL INTEGRATION TEST SUITE:
python -m pytest tests/integration -v

5) ACCEPTANCE TEST COMMANDS:
python -m pytest tests/acceptance/platform/test_ollama_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_approval_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_request_acceptance.py -v
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_review_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_request_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_results_acceptance.py -v
python -m pytest tests/acceptance/agents/research/test_research_agent_ui_end_to_end_acceptance.py -v

6) FULL ACCEPTANCE TEST SUITE:
python -m pytest tests/acceptance -v

7) BROWSER DEBUG COMMAND EXAMPLE:
python -m pytest tests/acceptance/agents/documentation/test_documentation_agent_ui_request_acceptance.py -v -s --headed --ui-slowmo=1000

8) START DASHBOARD AT PORT 8001:
python -m project0.dashboard.dashboard_app

9) REGRESSION BASELINE:
python -m pytest


