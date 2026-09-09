# ============================================================
# Project0 - Documentation Workflow Tests
#
# File: test_documentation_workflow.py
#
# Purpose:
#     Verify orchestration behavior for the Project0
#     documentation update workflow.
#
# ============================================================

from datetime import UTC, datetime
from pathlib import Path

from project0.interfaces.artifact_interfaces import (
    ArtifactLocationServiceInterface,
)
from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
)
from project0.models.documentation_workflow_models import (
    AppliedDocumentationChange,
    ChangeApplicationStatus,
    DocumentationAnchorMode,
    DocumentationChangeProposal,
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
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)
from project0.workflow.documentation_workflow import DocumentationWorkflow


class StubReasoningService:
    """Return a configured reasoning result."""

    def __init__(self, result: ReasoningResult) -> None:
        self._result = result
        self.requests: list[ReasoningRequest] = []

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        self.requests.append(request)
        return self._result


class StubArtifactLocationService:
    """Return configured artifact locations."""

    def __init__(
        self,
        locations: tuple[ArtifactLocation, ...] = (),
        locations_by_request: dict[
            str,
            tuple[ArtifactLocation, ...],
        ] | None = None,
    ) -> None:
        self._locations = locations
        self._locations_by_request = locations_by_request or {}
        self.requests: list[tuple[Path, str]] = []

    def discover_locations(
        self,
        artifact_path: Path,
        request: str,
    ) -> tuple[ArtifactLocation, ...]:
        self.requests.append((artifact_path, request))

        return self._locations_by_request.get(
            request,
            self._locations,
        )


class StubValidationService:
    """Return configured validation results in sequence."""

    def __init__(
        self,
        results: tuple[ValidationResult, ...],
    ) -> None:
        self._results = list(results)
        self.requests: list[ValidationRequest] = []

    def validate(self, request: ValidationRequest) -> ValidationResult:
        self.requests.append(request)

        if not self._results:
            raise RuntimeError("No validation result configured.")

        return self._results.pop(0)


class StubReviewCoordinator:
    """Return review decisions from a configured mapping."""

    def __init__(
        self,
        decisions: dict[str, ReviewDecision] | None = None,
    ) -> None:
        self._decisions = decisions or {}
        self.proposals: list[DocumentationChangeProposal] = []

    def review(
        self,
        proposal: DocumentationChangeProposal,
    ) -> DocumentationReview:
        self.proposals.append(proposal)

        return DocumentationReview(
            proposal_id=proposal.proposal_id,
            decision=self._decisions.get(
                proposal.repository_path,
                ReviewDecision.APPROVE,
            ),
            reviewed_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
        )


class StubRepositoryUpdateService:
    """Return configured application results."""

    def __init__(
        self,
        status_by_path: dict[str, ChangeApplicationStatus] | None = None,
    ) -> None:
        self._status_by_path = status_by_path or {}
        self.calls: list[
            tuple[DocumentationChangeProposal, DocumentationReview]
        ] = []

    def apply(
        self,
        proposal: DocumentationChangeProposal,
        review: DocumentationReview,
    ) -> AppliedDocumentationChange:
        self.calls.append((proposal, review))

        if review.decision is not ReviewDecision.APPROVE:
            status = ChangeApplicationStatus.SKIPPED
        else:
            status = self._status_by_path.get(
                proposal.repository_path,
                ChangeApplicationStatus.APPLIED,
            )

        return AppliedDocumentationChange(
            proposal_id=proposal.proposal_id,
            repository_path=proposal.repository_path,
            status=status,
            applied_at=(
                datetime(2026, 8, 5, 12, 1, tzinfo=UTC)
                if status is ChangeApplicationStatus.APPLIED
                else None
            ),
            error_message=(
                "Update failed."
                if status is ChangeApplicationStatus.FAILED
                else None
            ),
        )


class StubGitDiffService:
    """Return a configured Git diff or raise an error."""

    def __init__(
        self,
        diff: str = "diff output",
        error: Exception | None = None,
    ) -> None:
        self._diff = diff
        self._error = error
        self.requests: list[tuple[str, ...]] = []

    def generate_diff(
        self,
        repository_paths: tuple[str, ...] = (),
    ) -> str:
        self.requests.append(repository_paths)

        if self._error is not None:
            raise self._error

        return self._diff


def _reasoning_result(
    *,
    status: ReasoningStatus = ReasoningStatus.COMPLETED,
    proposed_changes: tuple[ProposedDocumentationChange, ...] = (),
    warnings: tuple[str, ...] = (),
    error_message: str | None = None,
) -> ReasoningResult:
    """Create a reasoning result for workflow tests."""

    return ReasoningResult(
        request_id="reasoning-001",
        status=status,
        summary="Reasoning summary.",
        impacts=(),
        proposed_changes=proposed_changes,
        created_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
        provider_name="stub",
        model_name="stub-model",
        warnings=warnings,
        error_message=error_message,
    )


def _validation_result(
    status: ValidationStatus,
    *,
    validation_id: str = "validation-001",
) -> ValidationResult:
    """Create a validation result for workflow tests."""

    timestamp = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

    return ValidationResult(
        validation_id=validation_id,
        status=status,
        started_at=timestamp,
        completed_at=timestamp,
        validator_results=(),
    )


def _update_change(
    repository_path: str = "docs/index.md",
    proposed_content: str = "# Updated\n",
    section: str | None = None,
    anchor_text: str | None = "# Original",
    edit_type: DocumentationEditType = DocumentationEditType.REPLACE,
) -> ProposedDocumentationChange:
    """Create an update reasoning proposal."""

    return ProposedDocumentationChange(
        document_path=Path(repository_path),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Update the document.",
        proposed_content=proposed_content,
        section=section,
        anchor_text=anchor_text,
        edit_type=edit_type,
    )


def _review(
    proposal: DocumentationChangeProposal,
    decision: ReviewDecision = ReviewDecision.APPROVE,
) -> DocumentationReview:
    """Create a browser-supplied review for a proposal."""

    return DocumentationReview(
        proposal_id=proposal.proposal_id,
        decision=decision,
        reviewed_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
    )


def _create_workflow(
    tmp_path: Path,
    *,
    reasoning_result: ReasoningResult,
    validation_results: tuple[ValidationResult, ...],
    decisions: dict[str, ReviewDecision] | None = None,
    status_by_path: dict[str, ChangeApplicationStatus] | None = None,
    git_diff: str = "diff output",
    git_error: Exception | None = None,
    context_provider=None,
    artifact_locations: tuple[ArtifactLocation, ...] = (),
    artifact_locations_by_request: dict[
        str,
        tuple[ArtifactLocation, ...],
    ] | None = None,
):
    """Create a workflow and its test doubles."""

    reasoning_service = StubReasoningService(reasoning_result)
    artifact_location_service = StubArtifactLocationService(
        artifact_locations,
        artifact_locations_by_request,
    )
    validation_service = StubValidationService(validation_results)
    review_coordinator = StubReviewCoordinator(decisions)
    update_service = StubRepositoryUpdateService(status_by_path)
    git_service = StubGitDiffService(git_diff, git_error)
    captured_context_requests: list[DocumentationWorkflowRequest] = []

    if context_provider is None:
        def context_provider(
            request: DocumentationWorkflowRequest,
        ) -> str:
            captured_context_requests.append(request)
            return "repository context"

    workflow = DocumentationWorkflow(
        repository_root=tmp_path,
        context_provider=context_provider,
        reasoning_service=reasoning_service,
        artifact_location_service=artifact_location_service,
        validation_service=validation_service,
        review_coordinator=review_coordinator,
        repository_update_service=update_service,
        git_diff_service=git_service,
    )

    return (
        workflow,
        reasoning_service,
        validation_service,
        review_coordinator,
        update_service,
        git_service,
        captured_context_requests,
    )


def test_approved_update_completes_workflow(tmp_path: Path) -> None:
    """An approved browser review completes the full workflow."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
            _validation_result(ValidationStatus.PASSED),
        ),
    )
    workflow = components[0]
    review_coordinator = components[3]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-001",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.proposals) == 1
    assert state.source_paths == ("src/project0/example.py",)
    assert state.reviews == ()
    assert state.applied_changes == ()
    assert review_coordinator.proposals == []

    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0]),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert result.source_paths == ("src/project0/example.py",)
    assert len(result.proposals) == 1
    assert len(result.reviews) == 1
    assert len(result.applied_changes) == 1
    assert result.summary.proposed_count == 1
    assert result.summary.approved_count == 1
    assert result.summary.applied_count == 1
    assert result.git_diff == "diff output"
    assert result.error_message is None



def test_revise_review_preserves_request_context(
    tmp_path: Path,
) -> None:
    """A revise decision returns review state with request context."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update the documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-revise",
        )
    )

    revised_state = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0], ReviewDecision.REVISE),
    )

    assert revised_state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert revised_state.user_request == "Update the documentation."
    assert revised_state.target_paths == ("docs/index.md",)
    assert revised_state.source_paths == ("src/project0/example.py",)
    assert revised_state.reviews[0].decision is ReviewDecision.REVISE
    assert revised_state.applied_changes == ()


def test_anchor_text_is_propagated_to_workflow_proposal(
    tmp_path: Path,
) -> None:
    """Reasoning anchor text is preserved in workflow proposals."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n## Existing Section\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    anchor_text="## Existing Section",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-anchor-text",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.proposals) == 1
    assert state.proposals[0].anchor_text == "## Existing Section"


def test_insert_edit_type_is_propagated_to_proposal_anchor_mode(
    tmp_path: Path,
) -> None:
    """Insert edit intent becomes an insert-after workflow proposal."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "Implemented:\n\n- Existing item.\n",
        encoding="utf-8",
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    anchor_text="Implemented:",
                    edit_type=DocumentationEditType.INSERT,
                    proposed_content="- New item.",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Insert documentation.",
            workflow_id="workflow-insert-mode",
        )
    )

    assert state.proposals[0].anchor_mode is (
        DocumentationAnchorMode.INSERT_AFTER
    )



def test_context_and_reasoning_request_are_forwarded(
    tmp_path: Path,
) -> None:
    """The workflow request is converted into a reasoning request."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )
    workflow, reasoning_service = components[0], components[1]
    captured_context_requests = components[6]

    request = DocumentationWorkflowRequest(
        user_request="Review the documentation.",
        target_paths=("docs/index.md",),
        source_paths=("src/project0/example.py",),
        workflow_id="workflow-002",
    )

    workflow.execute(request)

    assert captured_context_requests == [request]
    assert len(reasoning_service.requests) == 1

    reasoning_request = reasoning_service.requests[0]

    assert reasoning_request.objective == "Review the documentation."
    assert reasoning_request.context == "repository context"
    assert reasoning_request.workflow_type == "documentation_update"
    assert reasoning_request.target_paths == (Path("docs/index.md"),)
    assert (
        "Ground Truth Source Paths are read-only authoritative evidence "
        "and must not be proposed for modification."
        in reasoning_request.constraints
    )
    assert (
        "When target documentation paths are provided, propose changes "
        "only to those target paths."
        in reasoning_request.constraints
    )
    assert reasoning_request.metadata["workflow_id"] == "workflow-002"


def test_reasoning_failure_stops_workflow(tmp_path: Path) -> None:
    """A failed reasoning result stops validation and review."""

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            status=ReasoningStatus.FAILED,
            error_message="Reasoning failed.",
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]
    review_coordinator = components[3]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
        )
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.error_message == "Reasoning failed."
    assert validation_service.requests == []
    assert review_coordinator.proposals == []


def test_preliminary_validation_failure_stops_review(
    tmp_path: Path,
) -> None:
    """Failed preliminary validation prevents user review."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.FAILED),
        ),
    )
    workflow = components[0]
    review_coordinator = components[3]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
        )
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.error_message == (
        "Preliminary documentation validation failed."
    )
    assert len(result.proposals) == 1
    assert review_coordinator.proposals == []


def test_preliminary_warning_is_preserved(tmp_path: Path) -> None:
    """Preliminary validation warnings survive browser review."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(
                ValidationStatus.PASSED_WITH_WARNINGS
            ),
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-warning",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert (
        "Preliminary validation completed with warnings."
        in state.warnings
    )

    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0]),
    )

    assert (
        result.status
        is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
    )
    assert (
        "Preliminary validation completed with warnings."
        in result.warnings
    )


def test_proposal_outside_requested_target_scope_is_skipped(
    tmp_path: Path,
) -> None:
    """Explicit target paths should bound the documentation write scope."""

    allowed = tmp_path / "docs/allowed.md"
    other = tmp_path / "docs/other.md"
    allowed.parent.mkdir()
    allowed.write_text("# Allowed\n", encoding="utf-8")
    other.write_text("# Other\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    "docs/other.md",
                    "# Other Updated\n",
                ),
            )
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update only the allowed document.",
            target_paths=("docs/allowed.md",),
            workflow_id="workflow-target-scope",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "outside the requested target scope"
        in warning
        for warning in result.warnings
    )


def test_unsupported_create_operation_is_skipped(
    tmp_path: Path,
) -> None:
    """Unsupported create proposals are skipped with a warning."""

    create_change = ProposedDocumentationChange(
        document_path=Path("docs/new.md"),
        operation=DocumentationChangeOperation.CREATE,
        rationale="Create a document.",
        proposed_content="# New\n",
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(create_change,)
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Create documentation.",
        )
    )

    assert result.proposals == ()
    assert result.reviews == ()
    assert result.applied_changes == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert result.git_diff == ""
    assert (
        result.status
        is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
    )
    assert "Unsupported documentation operation was skipped" in (
        result.warnings[0]
    )


def test_non_markdown_proposal_is_skipped(tmp_path: Path) -> None:
    """A non-Markdown update proposal is skipped."""

    target = tmp_path / "config.txt"
    target.write_text("original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    repository_path="config.txt",
                    proposed_content="updated\n",
                ),
            )
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update configuration.",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert "Proposed non-Markdown change was skipped" in (
        result.warnings[0]
    )


def test_review_decisions_are_summarized(tmp_path: Path) -> None:
    """Browser review decisions produce correct summary counts."""

    first = tmp_path / "docs/first.md"
    second = tmp_path / "docs/second.md"
    first.parent.mkdir()
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change("docs/first.md", "# First Updated\n"),
                _update_change("docs/second.md", "# Second Updated\n"),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documents.",
            workflow_id="workflow-review-summary",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.proposals) == 2

    state = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0], ReviewDecision.APPROVE),
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.reviews) == 1
    assert len(state.applied_changes) == 1

    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[1], ReviewDecision.REJECT),
    )

    assert result.summary.proposed_count == 2
    assert result.summary.approved_count == 1
    assert result.summary.rejected_count == 1
    assert result.summary.applied_count == 1
    assert result.git_diff == "diff output"


def test_no_approved_changes_skip_final_validation_and_diff(
    tmp_path: Path,
) -> None:
    """Rejected proposals do not trigger final validation or Git diff."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )
    workflow = components[0]
    validation_service = components[2]
    git_service = components[5]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-reject",
        )
    )
    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0], ReviewDecision.REJECT),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert len(validation_service.requests) == 1
    assert git_service.requests == []
    assert result.final_validation is None
    assert result.git_diff == ""


def test_repository_update_failure_fails_workflow(
    tmp_path: Path,
) -> None:
    """A failed approved browser update fails the workflow."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
        status_by_path={
            "docs/index.md": ChangeApplicationStatus.FAILED,
        },
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-update-failure",
        )
    )
    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0]),
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.summary.failed_count == 1
    assert result.summary.applied_count == 0
    assert result.error_message == (
        "One or more approved documentation changes failed."
    )


def test_final_validation_failure_fails_workflow(
    tmp_path: Path,
) -> None:
    """A failed final validation produces a failed result."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
            _validation_result(ValidationStatus.FAILED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-final-validation",
        )
    )
    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0]),
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert (
        "Final validation failed after approved documentation "
        "changes were applied."
        in result.warnings
    )


def test_git_diff_error_is_raised_during_review_completion(
    tmp_path: Path,
) -> None:
    """A Git diff error occurs when the final review completes."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(_update_change(),)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
            _validation_result(ValidationStatus.PASSED),
        ),
        git_error=RuntimeError("Git diff failed."),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-git-error",
        )
    )

    try:
        workflow.submit_review(
            state.workflow_id,
            _review(state.proposals[0]),
        )
    except RuntimeError as error:
        assert str(error) == "Git diff failed."
    else:
        raise AssertionError("Expected Git diff failure.")


def test_unknown_workflow_review_is_rejected(tmp_path: Path) -> None:
    """A review cannot be submitted for an unknown workflow."""

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    review = DocumentationReview(
        proposal_id="proposal-unknown",
        decision=ReviewDecision.APPROVE,
        reviewed_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
    )

    try:
        workflow.submit_review("workflow-missing", review)
    except ValueError as error:
        assert "workflow state was not found" in str(error)
    else:
        raise AssertionError("Expected missing workflow failure.")


def test_duplicate_review_is_rejected(tmp_path: Path) -> None:
    """A proposal cannot be reviewed twice."""

    first = tmp_path / "docs/first.md"
    second = tmp_path / "docs/second.md"
    first.parent.mkdir()
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change("docs/first.md"),
                _update_change("docs/second.md"),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    state = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documents.",
            workflow_id="workflow-duplicate",
        )
    )
    first_review = _review(state.proposals[0])
    state = workflow.submit_review(state.workflow_id, first_review)

    try:
        workflow.submit_review(state.workflow_id, first_review)
    except ValueError as error:
        assert "already been reviewed" in str(error)
    else:
        raise AssertionError("Expected duplicate review failure.")


def test_context_provider_error_is_converted_to_failed_result(
    tmp_path: Path,
) -> None:
    """A context provider error is returned as a workflow failure."""

    def failing_context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        raise ValueError("Context failed.")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
        context_provider=failing_context_provider,
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
        )
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.error_message == "Context failed."
    assert result.summary.proposed_count == 0


def test_reasoning_warnings_are_preserved(tmp_path: Path) -> None:
    """Reasoning warnings produce completed-with-warnings status."""

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            warnings=("Reasoning warning.",)
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
        )
    )

    assert (
        result.status
        is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert result.warnings == ("Reasoning warning.",)


def test_source_grounded_workflow_omits_unverified_reasoning_warnings(
    tmp_path: Path,
) -> None:
    """Source-grounded runs omit free-form model repository warnings."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    reasoning_result = _reasoning_result(
        warnings=("Unverified repository warning.",)
    )
    reasoning_result = ReasoningResult(
        request_id=reasoning_result.request_id,
        status=reasoning_result.status,
        summary=reasoning_result.summary,
        impacts=reasoning_result.impacts,
        proposed_changes=reasoning_result.proposed_changes,
        created_at=reasoning_result.created_at,
        provider_name=reasoning_result.provider_name,
        model_name=reasoning_result.model_name,
        warnings=reasoning_result.warnings,
        metadata={
            "provider_warnings": (),
            "response_warnings": (
                "Unverified repository warning.",
            ),
        },
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=reasoning_result,
        validation_results=(),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-source-grounded-warning",
        )
    )

    assert result.warnings == ()
    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED


def test_source_grounded_workflow_preserves_provider_warnings(
    tmp_path: Path,
) -> None:
    """Source-grounded runs retain provider execution warnings."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    reasoning_result = _reasoning_result(
        warnings=("Provider warning.", "Reasoning warning.")
    )
    reasoning_result = ReasoningResult(
        request_id=reasoning_result.request_id,
        status=reasoning_result.status,
        summary=reasoning_result.summary,
        impacts=reasoning_result.impacts,
        proposed_changes=reasoning_result.proposed_changes,
        created_at=reasoning_result.created_at,
        provider_name=reasoning_result.provider_name,
        model_name=reasoning_result.model_name,
        warnings=reasoning_result.warnings,
        metadata={
            "provider_warnings": ("Provider warning.",),
            "response_warnings": ("Reasoning warning.",),
        },
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=reasoning_result,
        validation_results=(),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-provider-warning",
        )
    )

    assert result.warnings == ("Provider warning.",)


def test_non_source_grounded_unresolved_anchor_remains_reviewable(
    tmp_path: Path,
) -> None:
    """Ordinary requests preserve legacy proposal review behavior."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\nExisting text.\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    section="Missing Section",
                    anchor_text="Missing anchor.",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            workflow_id="workflow-non-source-grounded-anchor",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert result.proposals[0].artifact_location is None
    assert result.proposals[0].anchor_text == "Missing anchor."


def test_proposal_with_missing_anchor_and_no_location_is_skipped(
    tmp_path: Path,
) -> None:
    """Unlocatable updates fail closed instead of reaching review."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\nExisting text.\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    section="Missing Section",
                    anchor_text="Missing anchor.",
                ),
            )
        ),
        validation_results=(),
    )

    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-missing-anchor",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "anchor text was not found"
        in warning
        for warning in result.warnings
    )


def test_proposal_with_ambiguous_anchor_and_no_location_is_skipped(
    tmp_path: Path,
) -> None:
    """Ambiguous anchor text fails closed instead of selecting one."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\nRepeated text.\nRepeated text.\n",
        encoding="utf-8",
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    anchor_text="Repeated text.",
                ),
            )
        ),
        validation_results=(),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-ambiguous-anchor",
        )
    )

    assert result.proposals == ()
    assert any(
        "anchor text was ambiguous"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_semantically_misaligned_section_recovers(
    tmp_path: Path,
) -> None:
    """A wrong selected section recovers to one clear semantic match."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Context details.\n"
        "## Research Analysis Validation Interface Behavior\n"
        "Validation details.\n"
        "## Revision Workflow Interface Behavior\n"
        "Revision details.\n",
        encoding="utf-8",
    )

    validation_location = ArtifactLocation(
        location_id="location-validation",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Research Analysis Validation Interface Behavior",
        start_line=4,
        end_line=5,
        content_hash="validation-hash",
    )
    context_location = ArtifactLocation(
        location_id="location-context",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Existing Research Context Interface Contract",
        start_line=2,
        end_line=3,
        content_hash="context-hash",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale=(
            "Update ResearchWorkflowProtocol.execute to support "
            "existing research context."
        ),
        proposed_content=(
            "```python\n"
            "def execute(\n"
            "    self,\n"
            "    context_source_name=None,\n"
            "    context_content=None,\n"
            "):\n"
            "    pass\n"
            "```"
        ),
        section="Research Analysis Validation Interface Behavior",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
        artifact_locations_by_request={
            "Research Analysis Validation Interface Behavior": (
                validation_location,
            ),
            "Existing Research Context Interface Contract": (
                context_location,
            ),
        },
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-semantic-recovery",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert result.proposals[0].artifact_location == context_location
    assert result.warnings == ()


def test_source_grounded_semantic_recovery_fails_on_tied_candidates(
    tmp_path: Path,
) -> None:
    """Tied semantic candidates fail closed rather than guessing."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Context Contract\n"
        "Context details.\n"
        "## Context Reference\n"
        "More context details.\n"
        "## Validation Behavior\n"
        "Validation details.\n",
        encoding="utf-8",
    )

    validation_location = ArtifactLocation(
        location_id="location-validation",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Validation Behavior",
        start_line=6,
        end_line=7,
        content_hash="validation-hash",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document context handling.",
        proposed_content="Context handling details.",
        section="Validation Behavior",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(),
        artifact_locations_by_request={
            "Validation Behavior": (
                validation_location,
            ),
        },
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-semantic-recovery-tie",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "no unambiguous replacement section was found"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_semantic_recovery_requires_resolved_location(
    tmp_path: Path,
) -> None:
    """A recovered heading must resolve to one concrete location."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Context details.\n"
        "## Validation Behavior\n"
        "Validation details.\n",
        encoding="utf-8",
    )

    validation_location = ArtifactLocation(
        location_id="location-validation",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Validation Behavior",
        start_line=4,
        end_line=5,
        content_hash="validation-hash",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content="Context handling details.",
        section="Validation Behavior",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(),
        artifact_locations_by_request={
            "Validation Behavior": (
                validation_location,
            ),
            "Existing Research Context Interface Contract": (),
        },
    )
    workflow = components[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-semantic-recovery-unresolved",
        )
    )

    assert result.proposals == ()
    assert any(
        "replacement section could not be resolved unambiguously"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_semantically_aligned_section_is_reviewable(
    tmp_path: Path,
) -> None:
    """A selected section sharing meaningful subject terms is retained."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Context details.\n",
        encoding="utf-8",
    )

    location = ArtifactLocation(
        location_id="location-context",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Existing Research Context Interface Contract",
        start_line=2,
        end_line=3,
        content_hash="hash",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale=(
            "Document existing research context handling for "
            "ResearchWorkflowProtocol.execute."
        ),
        proposed_content=(
            "```python\n"
            "def execute(self, context_source_name=None):\n"
            "    pass\n"
            "```"
        ),
        section="Existing Research Context Interface Contract",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
        artifact_locations=(location,),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-semantic-match",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert result.proposals[0].artifact_location == location
    assert not any(
        "not semantically aligned"
        in warning
        for warning in result.warnings
    )


def test_section_semantic_tokens_split_identifiers_and_ignore_generic_terms() -> None:
    """Semantic tokens normalize snake/camel identifiers consistently."""

    tokens = DocumentationWorkflow._semantic_tokens(
        "ResearchWorkflowProtocol context_source_name"
    )

    assert "workflow" in tokens
    assert "protocol" in tokens
    assert "context" in tokens
    assert "source" in tokens
    assert "name" in tokens
    assert "research" not in tokens


def test_select_recovery_section_returns_unique_highest_match() -> None:
    """Recovery selects the one subsection with greatest token overlap."""

    content = (
        "# Document\n"
        "## Existing Research Context Interface Contract\n"
        "## Research Analysis Validation Interface Behavior\n"
        "## Revision Workflow Interface Behavior\n"
    )

    section = DocumentationWorkflow._select_recovery_section(
        original_content=content,
        rationale=(
            "Update ResearchWorkflowProtocol.execute for existing "
            "research context."
        ),
        proposed_content="context_source_name context_content",
    )

    assert section == "Existing Research Context Interface Contract"


def test_select_recovery_section_returns_none_for_tie() -> None:
    """Recovery refuses tied best candidates."""

    content = (
        "# Document\n"
        "## Existing Context\n"
        "## Context Handling\n"
    )

    section = DocumentationWorkflow._select_recovery_section(
        original_content=content,
        rationale="Document context.",
        proposed_content="Context details.",
    )

    assert section is None


def test_extract_recovery_section_headings_excludes_document_title() -> None:
    """Recovery candidates exclude H1 titles and deduplicate headings."""

    headings = DocumentationWorkflow._extract_recovery_section_headings(
        "# Document\n"
        "## Context\n"
        "### Validation\n"
        "## Context\n"
    )

    assert headings == (
        "Context",
        "Validation",
    )


def test_workflow_timestamps_are_timezone_aware(
    tmp_path: Path,
) -> None:
    """Workflow result timestamps are timezone-aware."""

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
        )
    )

    assert result.started_at.tzinfo is UTC
    assert result.completed_at.tzinfo is UTC
    assert result.completed_at >= result.started_at


def test_artifact_location_service_uses_section_for_proposals(
    tmp_path: Path,
) -> None:
    """Structured section should be the preferred location request."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n## Interfaces\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    section="Interfaces",
                    anchor_text="Existing interface text.",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )

    workflow = components[0]
    artifact_location_service = workflow._artifact_location_service

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-artifact-location-section",
        )
    )

    assert artifact_location_service.requests == [
        (document.resolve(), "Interfaces"),
        (document.resolve(), "Update the document."),
    ]


def test_artifact_location_service_uses_rationale_when_anchor_exists(
    tmp_path: Path,
) -> None:
    """Anchor text should not be used for section discovery."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\nExisting text.\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    anchor_text="Existing text.",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )

    workflow = components[0]
    artifact_location_service = workflow._artifact_location_service

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-artifact-location-anchor",
        )
    )

    assert artifact_location_service.requests == [
        (document.resolve(), "Update the document."),
    ]


def test_artifact_location_service_falls_back_to_rationale(
    tmp_path: Path,
) -> None:
    """Rationale should be used only when no structured location exists."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    anchor_text=None,
                ),
            )
        ),
        validation_results=(),
    )

    workflow = components[0]
    artifact_location_service = workflow._artifact_location_service

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            workflow_id="workflow-artifact-location-rationale",
        )
    )

    assert artifact_location_service.requests == [
        (document.resolve(), "Update the document."),
    ]
