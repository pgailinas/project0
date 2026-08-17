# ============================================================
# Project0 - Documentation Workflow Flow Tests
#
# File: test_documentation_workflow_flow.py
#
# Purpose:
#     Verify the complete Project0 documentation workflow using
#     real Phase 5 and Phase 6 service implementations.
#
# ============================================================

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
import subprocess

from project0.artifacts.artifact_location_service import (
    ArtifactLocationService,
)
from project0.models.documentation_workflow_models import (
    ChangeApplicationStatus,
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowStatus,
    ReviewDecision,
)
from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationEditType,
    ProposedDocumentationChange,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)
from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)
from project0.repository.git_diff_service import GitDiffService
from project0.repository.repository_update_service import (
    RepositoryUpdateService,
)
from project0.validation.validation_service import ValidationService
from project0.workflow.documentation_workflow import DocumentationWorkflow
from project0.workflow.review_coordinator import ReviewCoordinator


class StubReasoningService:
    """Return a deterministic reasoning result."""

    def __init__(
        self,
        proposed_changes: tuple[ProposedDocumentationChange, ...],
        *,
        status: ReasoningStatus = ReasoningStatus.COMPLETED,
        warnings: tuple[str, ...] = (),
        error_message: str | None = None,
    ) -> None:
        self._proposed_changes = proposed_changes
        self._status = status
        self._warnings = warnings
        self._error_message = error_message
        self.requests: list[ReasoningRequest] = []

    def reason(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResult:
        """Return the configured reasoning result."""

        self.requests.append(request)

        return ReasoningResult(
            request_id="reasoning-integration-001",
            status=self._status,
            summary="Integration reasoning result.",
            impacts=(),
            proposed_changes=self._proposed_changes,
            created_at=datetime(2026, 8, 5, 13, 0, tzinfo=UTC),
            provider_name="stub",
            model_name="stub-model",
            warnings=self._warnings,
            error_message=self._error_message,
        )


class FileContentValidator:
    """Validate that selected Markdown files contain valid content."""

    validator_name = "file_content"

    def __init__(
        self,
        repository_root: Path,
        *,
        fail_on_text: str | None = None,
        warn_on_text: str | None = None,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._fail_on_text = fail_on_text
        self._warn_on_text = warn_on_text

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Validate selected repository files."""

        timestamp = datetime(2026, 8, 5, 13, 0, tzinfo=UTC)
        issues: list[ValidationIssue] = []

        for repository_path in request.target_paths:
            file_path = self._repository_root / repository_path
            content = file_path.read_text(encoding="utf-8")

            if (
                self._fail_on_text is not None
                and self._fail_on_text in content
            ):
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="disallowed-content",
                        message="The document contains disallowed content.",
                        repository_path=repository_path,
                    )
                )

            if (
                self._warn_on_text is not None
                and self._warn_on_text in content
            ):
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.WARNING,
                        code="warning-content",
                        message="The document contains warning content.",
                        repository_path=repository_path,
                    )
                )

        if any(
            issue.severity is ValidationSeverity.ERROR
            for issue in issues
        ):
            status = ValidationStatus.FAILED
        elif issues:
            status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            status = ValidationStatus.PASSED

        return ValidatorResult(
            validator_name=self.validator_name,
            status=status,
            started_at=timestamp,
            completed_at=timestamp,
            issues=tuple(issues),
        )


def _update_change(
    repository_path: str,
    proposed_content: str,
    edit_type: DocumentationEditType = DocumentationEditType.REPLACE,
) -> ProposedDocumentationChange:
    """Create a deterministic update proposal."""

    return ProposedDocumentationChange(
        document_path=Path(repository_path),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Update the documentation.",
        proposed_content=proposed_content,
        edit_type=edit_type,
    )


def _git_diff_runner(
    command: Sequence[str],
    working_directory: Path,
) -> subprocess.CompletedProcess[str]:
    """Return a deterministic Git diff result."""

    selected_paths = tuple(command[4:])
    diff_lines = tuple(
        f"diff --git a/{path} b/{path}"
        for path in selected_paths
    )

    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout="\n".join(diff_lines),
        stderr="",
    )


def _review(
    proposal_id: str,
    decision: ReviewDecision,
    feedback: str | None = None,
) -> DocumentationReview:
    """Create a deterministic interactive workflow review."""

    return DocumentationReview(
        proposal_id=proposal_id,
        decision=decision,
        feedback=feedback,
        reviewed_at=datetime(2026, 8, 5, 13, 5, tzinfo=UTC),
    )


def _create_workflow(
    repository_root: Path,
    reasoning_service: StubReasoningService,
    *,
    validator: FileContentValidator | None = None,
    git_runner=_git_diff_runner,
) -> DocumentationWorkflow:
    """Create the real documentation workflow integration pipeline."""

    artifact_location_service = ArtifactLocationService()

    validation_service = ValidationService(
        validators=(
            validator or FileContentValidator(repository_root),
        )
    )

    return DocumentationWorkflow(
        repository_root=repository_root,
        context_provider=lambda request: (
            f"Workflow {request.workflow_id} repository context."
        ),
        reasoning_service=reasoning_service,
        artifact_location_service=artifact_location_service,
        validation_service=validation_service,
        review_coordinator=ReviewCoordinator(
            lambda proposal: (
                ReviewDecision.SKIP,
                "Interactive review is supplied explicitly.",
            )
        ),
        repository_update_service=RepositoryUpdateService(
            repository_root
        ),
        git_diff_service=GitDiffService(
            repository_root=repository_root,
            command_runner=git_runner,
        ),
    )


def test_approved_change_updates_file_and_returns_diff(
    tmp_path: Path,
) -> None:
    """An approved change completes the real workflow."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change("docs/index.md", "# Updated\n"),
        )
    )
    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the project index.",
            target_paths=("docs/index.md",),
            workflow_id="workflow-integration-001",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert document.read_text(encoding="utf-8") == "# Original\n"

    result = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[0].proposal_id,
            ReviewDecision.APPROVE,
        ),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert document.read_text(encoding="utf-8") == "# Updated\n"
    assert result.summary.proposed_count == 1
    assert result.summary.approved_count == 1
    assert result.summary.applied_count == 1
    assert result.applied_changes[0].status is (
        ChangeApplicationStatus.APPLIED
    )
    assert result.git_diff == (
        "diff --git a/docs/index.md b/docs/index.md"
    )


def test_insert_edit_type_reaches_repository_application(
    tmp_path: Path,
) -> None:
    """Insert edit intent reaches the repository update layer."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "Implemented:\n\n- Existing item.\n",
        encoding="utf-8",
    )

    workflow = _create_workflow(
        tmp_path,
        StubReasoningService(
            proposed_changes=(
                _update_change(
                    "docs/index.md",
                    "- New item.",
                ),
            )
        ),
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Insert documentation.",
            workflow_id="workflow-insert-flow",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED



def test_rejected_change_does_not_modify_repository(
    tmp_path: Path,
) -> None:
    """A rejected change leaves the repository unchanged."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change("docs/index.md", "# Updated\n"),
        )
    )
    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the project index.",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert document.read_text(encoding="utf-8") == "# Original\n"

    result = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[0].proposal_id,
            ReviewDecision.REJECT,
            "The update is not needed.",
        ),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert document.read_text(encoding="utf-8") == "# Original\n"
    assert result.summary.rejected_count == 1
    assert result.summary.applied_count == 0
    assert result.git_diff == ""
    assert result.final_validation is None


def test_preliminary_validation_failure_stops_review_and_update(
    tmp_path: Path,
) -> None:
    """Failed preliminary validation stops the workflow."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n\nDISALLOWED\n",
        encoding="utf-8",
    )

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change("docs/index.md", "# Updated\n"),
        )
    )
    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
        validator=FileContentValidator(
            tmp_path,
            fail_on_text="DISALLOWED",
        ),
    )

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the project index.",
        )
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.error_message == (
        "Preliminary documentation validation failed."
    )
    assert document.read_text(encoding="utf-8") == (
        "# Original\n\nDISALLOWED\n"
    )


def test_mixed_review_decisions_apply_only_approved_changes(
    tmp_path: Path,
) -> None:
    """Mixed decisions update only approved files."""

    first = tmp_path / "docs/first.md"
    second = tmp_path / "docs/second.md"
    third = tmp_path / "docs/third.md"
    first.parent.mkdir()
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")
    third.write_text("# Third\n", encoding="utf-8")

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change("docs/first.md", "# First Updated\n"),
            _update_change("docs/second.md", "# Second Updated\n"),
            _update_change("docs/third.md", "# Third Updated\n"),
        )
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update selected documentation.",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.proposals) == 3

    state = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[0].proposal_id,
            ReviewDecision.APPROVE,
        ),
    )
    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED

    state = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[1].proposal_id,
            ReviewDecision.REJECT,
        ),
    )
    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED

    result = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[2].proposal_id,
            ReviewDecision.SKIP,
        ),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert first.read_text(encoding="utf-8") == "# First Updated\n"
    assert second.read_text(encoding="utf-8") == "# Second\n"
    assert third.read_text(encoding="utf-8") == "# Third\n"
    assert result.summary.proposed_count == 3
    assert result.summary.approved_count == 1
    assert result.summary.rejected_count == 1
    assert result.summary.skipped_count == 1
    assert result.summary.applied_count == 1
    assert result.git_diff == (
        "diff --git a/docs/first.md b/docs/first.md"
    )


def test_final_validation_failure_is_reported_after_update(
    tmp_path: Path,
) -> None:
    """Final validation failure is reported after an applied update."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change(
                "docs/index.md",
                "# Updated\n\nDISALLOWED\n",
            ),
        )
    )
    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
        validator=FileContentValidator(
            tmp_path,
            fail_on_text="DISALLOWED",
        ),
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the project index.",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED

    result = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[0].proposal_id,
            ReviewDecision.APPROVE,
        ),
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert document.read_text(encoding="utf-8") == (
        "# Updated\n\nDISALLOWED\n"
    )
    assert result.final_validation is not None
    assert result.final_validation.status is ValidationStatus.FAILED
    assert (
        "Final validation failed after approved documentation "
        "changes were applied."
        in result.warnings
    )


def test_validation_warning_produces_completed_with_warnings(
    tmp_path: Path,
) -> None:
    """Validation warnings propagate through the real workflow."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n\nWARNING\n",
        encoding="utf-8",
    )

    reasoning_service = StubReasoningService(
        proposed_changes=(
            _update_change(
                "docs/index.md",
                "# Updated\n\nWARNING\n",
            ),
        )
    )
    workflow = _create_workflow(
        tmp_path,
        reasoning_service,
        validator=FileContentValidator(
            tmp_path,
            warn_on_text="WARNING",
        ),
    )

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the project index.",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert (
        "Preliminary validation completed with warnings."
        in state.warnings
    )

    result = workflow.submit_review(
        state.workflow_id,
        _review(
            state.proposals[0].proposal_id,
            ReviewDecision.APPROVE,
        ),
    )

    assert (
        result.status
        is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
    )
    assert document.read_text(encoding="utf-8") == (
        "# Updated\n\nWARNING\n"
    )
    assert (
        "Preliminary validation completed with warnings."
        in result.warnings
    )
    assert (
        "Final validation completed with warnings."
        in result.warnings
    )
