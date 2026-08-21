# ============================================================
# Project0 - Platform Dispatcher
#
# File: platform_dispatcher.py
#
# Purpose:
#     Assemble Project0 platform services and coordinate
#     platform-level workflow execution.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


from project0.artifacts.artifact_location_service import (
    ArtifactLocationService,
)
from project0.agents.research.paper_metadata_service import (
    PaperMetadataService,
)
from project0.agents.research.research_artifact_service import (
    ResearchArtifactService,
)
from project0.agents.research.research_evaluation_service import (
    ResearchEvaluationService,
)
from project0.agents.research.research_source_service import (
    ResearchSourceService,
)
from project0.agents.research.research_strategy_service import (
    ResearchStrategyService,
)
from project0.common.startup_validation import validate_startup
from project0.config.settings import SETTINGS, ProjectSettings
from project0.interfaces.context_builder_interfaces import (
    ContextBuilderInterface,
)
from project0.interfaces.documentation_workflow_interfaces import (
    DocumentationWorkflowInterface,
)
from project0.interfaces.reasoning_interfaces import (
    ReasoningProviderProtocol,
)
from project0.interfaces.research_interfaces import (
    ResearchWorkflowProtocol,
)
from project0.interfaces.repository_interfaces import RepositoryInterface
from project0.interfaces.workflow_interfaces import WorkflowInterface
from project0.knowledge.context_builder import ContextBuilder
from project0.knowledge.knowledge_service import KnowledgeService
from project0.models.context_models import ContextWorkflowType
from project0.models.documentation_workflow_models import (
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
    DocumentationWorkflowState,
)
from project0.models.knowledge_models import KnowledgeRequest
from project0.models.research_models import (
    ResearchRequest,
    ResearchResult,
)
from project0.models.workflow_models import (
    WorkflowExecutionResult,
    WorkflowTask,
)
from project0.reasoning.prompt_builder import PromptBuilder
from project0.reasoning.reasoning_service import ReasoningService
from project0.repository.git_diff_service import GitDiffService
from project0.repository.repository_service import RepositoryService
from project0.repository.repository_update_service import (
    RepositoryUpdateService,
)
from project0.validation.link_validator import LinkValidator
from project0.validation.markdown_validator import MarkdownValidator
from project0.validation.mkdocs_validator import MkDocsValidator
from project0.validation.validation_service import ValidationService
from project0.workflow.documentation_workflow import DocumentationWorkflow
from project0.workflow.research_workflow import ResearchWorkflow
from project0.workflow.review_coordinator import (
    ReviewCoordinator,
    ReviewDecisionProvider,
)
from project0.workflow.workflow_engine import WorkflowEngine


@dataclass(slots=True)
class PlatformDispatcher:
    """Coordinate Project0 platform services."""

    repository: RepositoryInterface
    context_builder: ContextBuilderInterface
    workflow_engine: WorkflowInterface
    documentation_workflow: DocumentationWorkflowInterface | None = None
    research_workflow: ResearchWorkflowProtocol | None = None

    def run_context_workflow(
        self,
        context_id: str,
        workflow_type: ContextWorkflowType,
        workflow_name: str = "Build Project0 Context",
        workflow_id: str | None = None,
    ) -> WorkflowExecutionResult:
        """Build workflow-specific context through the Workflow Engine."""

        if not context_id.strip():
            raise ValueError("Context identifier cannot be empty.")

        if not workflow_name.strip():
            raise ValueError("Workflow name cannot be empty.")

        resolved_workflow_id = workflow_id or str(uuid4())

        context_task = WorkflowTask(
            name="Build Documentation Context",
            action=lambda: self.context_builder.build_documentation_context(
                context_id=context_id,
                workflow_type=workflow_type,
            ),
        )

        return self.workflow_engine.execute(
            workflow_name=workflow_name,
            tasks=[context_task],
            workflow_id=resolved_workflow_id,
        )

    def run_documentation_workflow(
        self,
        user_request: str,
        target_paths: tuple[str, ...] = (),
        workflow_id: str | None = None,
    ) -> DocumentationWorkflowState | DocumentationWorkflowResult:
        """Execute the configured documentation workflow until review."""

        if self.documentation_workflow is None:
            raise RuntimeError(
                "The documentation workflow is not configured."
            )

        if not user_request.strip():
            raise ValueError("User request cannot be empty.")

        return self.documentation_workflow.execute(
            DocumentationWorkflowRequest(
                user_request=user_request,
                target_paths=target_paths,
                workflow_id=workflow_id or str(uuid4()),
            )
        )

    def run_research_workflow(
        self,
        question: str,
        constraints: tuple[str, ...] = (),
        focus_areas: tuple[str, ...] = (),
        source_names: tuple[str, ...] = (),
    ) -> ResearchResult:
        """Execute the configured Research Agent workflow."""

        if self.research_workflow is None:
            raise RuntimeError(
                "The research workflow is not configured."
            )

        if not question.strip():
            raise ValueError("Research question cannot be empty.")

        return self.research_workflow.execute(
            ResearchRequest(
                question=question,
                constraints=constraints,
                focus_areas=focus_areas,
                source_names=source_names,
            )
        )

    def submit_documentation_review(
        self,
        workflow_id: str,
        review: DocumentationReview,
    ) -> DocumentationWorkflowState | DocumentationWorkflowResult:
        """Submit a user review to the configured documentation workflow."""

        if self.documentation_workflow is None:
            raise RuntimeError(
                "The documentation workflow is not configured."
            )

        if not workflow_id.strip():
            raise ValueError("Workflow identifier cannot be empty.")

        return self.documentation_workflow.submit_review(
            workflow_id,
            review,
        )

    def get_workflow_state(
        self,
        workflow_id: str,
    ) -> DocumentationWorkflowState:
        """Retrieve the current documentation workflow state."""

        if self.documentation_workflow is None:
            raise RuntimeError(
                "The documentation workflow is not configured."
            )

        if not workflow_id.strip():
            raise ValueError("Workflow identifier cannot be empty.")

        return self.documentation_workflow.get_workflow_state(
            workflow_id,
        )

    def get_documentation_workflow_state(
        self,
        workflow_id: str,
    ) -> DocumentationWorkflowState:
        """Backward-compatible alias for documentation workflow state lookup."""

        return self.get_workflow_state(workflow_id)


def create_platform_dispatcher(
    reasoning_provider: ReasoningProviderProtocol | None = None,
    reasoning_model_name: str | None = None,
    review_decision_provider: ReviewDecisionProvider | None = None,
    settings: ProjectSettings | None = None,
) -> PlatformDispatcher:
    """Validate startup and assemble the default Project0 platform.

    A custom settings object may be supplied for isolated test
    environments. When omitted, the shared Project0 SETTINGS instance
    is used.
    """

    resolved_settings = settings or SETTINGS

    validate_startup(resolved_settings)

    repository_root = resolved_settings.project_root

    repository = RepositoryService(
        repository_root=repository_root
    )
    context_builder = ContextBuilder(
        repository_service=repository
    )
    workflow_engine = WorkflowEngine()

    documentation_workflow = _create_documentation_workflow(
        repository_root=repository_root,
        reasoning_provider=reasoning_provider,
        reasoning_model_name=reasoning_model_name,
        review_decision_provider=review_decision_provider,
    )

    research_workflow = _create_research_workflow(
        reasoning_provider=reasoning_provider,
        reasoning_model_name=reasoning_model_name,
    )

    return PlatformDispatcher(
        repository=repository,
        context_builder=context_builder,
        workflow_engine=workflow_engine,
        documentation_workflow=documentation_workflow,
        research_workflow=research_workflow,
    )


def _interactive_review_decision_provider(
    proposal,
):
    """Reject unexpected automatic review in interactive UI workflows."""

    raise RuntimeError(
        "Interactive documentation review requires a user decision."
    )


def _create_documentation_workflow(
    repository_root: Path,
    reasoning_provider: ReasoningProviderProtocol | None,
    reasoning_model_name: str | None,
    review_decision_provider: ReviewDecisionProvider | None,
) -> DocumentationWorkflowInterface | None:
    """Assemble the documentation workflow when dependencies are supplied."""

    if reasoning_provider is None:
        if review_decision_provider is None:
            return None

        raise ValueError(
            "A reasoning provider is required to configure "
            "the documentation workflow."
        )

    knowledge_service = KnowledgeService(repository_root)

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        knowledge_result = knowledge_service.build_knowledge(
            KnowledgeRequest(
                query=request.user_request,
                requested_paths=tuple(
                    Path(repository_path)
                    for repository_path in request.target_paths
                ),
                include_baseline_documents=False,
            )
        )

        return knowledge_result.context

    reasoning_service = ReasoningService(
        prompt_builder=PromptBuilder(
            model_name=reasoning_model_name,
        ),
        provider=reasoning_provider,
    )

    artifact_location_service = ArtifactLocationService()

    validation_service = ValidationService(
        validators=(
            MarkdownValidator(repository_root),
            LinkValidator(repository_root),
            MkDocsValidator(repository_root),
        )
    )

    return DocumentationWorkflow(
        repository_root=repository_root,
        context_provider=context_provider,
        reasoning_service=reasoning_service,
        artifact_location_service=artifact_location_service,
        validation_service=validation_service,
        review_coordinator=ReviewCoordinator(
            review_decision_provider
            or _interactive_review_decision_provider
        ),
        repository_update_service=RepositoryUpdateService(
            repository_root
        ),
        git_diff_service=GitDiffService(repository_root),
    )

def _create_research_workflow(
    reasoning_provider: ReasoningProviderProtocol | None,
    reasoning_model_name: str | None,
) -> ResearchWorkflowProtocol | None:
    """Assemble the research workflow when dependencies are supplied."""

    if reasoning_provider is None:
        return None

    if reasoning_model_name is None:
        raise ValueError(
            "A reasoning model name is required to configure "
            "the research workflow."
        )

    return ResearchWorkflow(
        strategy_service=ResearchStrategyService(),
        source_service=ResearchSourceService(),
        metadata_service=PaperMetadataService(),
        evaluation_service=ResearchEvaluationService(
            provider=reasoning_provider,
            model_name=reasoning_model_name,
        ),
        artifact_service=ResearchArtifactService(),
    )

