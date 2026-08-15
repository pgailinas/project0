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
    anchor_text: str | None = None,
    edit_type: DocumentationEditType = DocumentationEditType.REPLACE,
) -> ProposedDocumentationChange:
    """Create an update reasoning proposal."""

    return ProposedDocumentationChange(
        document_path=Path(repository_path),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Update the document.",
        proposed_content=proposed_content,
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
):
    """Create a workflow and its test doubles."""

    reasoning_service = StubReasoningService(reasoning_result)
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
            workflow_id="workflow-001",
        )
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(state.proposals) == 1
    assert state.reviews == ()
    assert state.applied_changes == ()
    assert review_coordinator.proposals == []

    result = workflow.submit_review(
        state.workflow_id,
        _review(state.proposals[0]),
    )

    assert result.status is DocumentationWorkflowStatus.COMPLETED
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

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(create_change,)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Create documentation.",
        )
    )

    assert result.proposals == ()
    assert result.reviews == ()
    assert result.applied_changes == ()
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

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    repository_path="config.txt",
                    proposed_content="updated\n",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update configuration.",
        )
    )

    assert result.proposals == ()
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

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            warnings=("Reasoning warning.",)
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
        )
    )

    assert (
        result.status
        is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.warnings == ("Reasoning warning.",)


def test_workflow_timestamps_are_timezone_aware(
    tmp_path: Path,
) -> None:
    """Workflow result timestamps are timezone-aware."""

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
        )
    )

    assert result.started_at.tzinfo is UTC
    assert result.completed_at.tzinfo is UTC
    assert result.completed_at >= result.started_at
