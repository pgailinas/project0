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
    DocumentationGap,
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
from project0.models.skill_models import SkillDefinition
from project0.workflow.documentation_workflow import DocumentationWorkflow


class StubReasoningService:
    """Return configured results for documentation reasoning stages."""

    def __init__(self, result: ReasoningResult) -> None:
        self._result = result
        self.requests: list[ReasoningRequest] = []

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        self.requests.append(request)

        if (
            request.workflow_type == "documentation_gap_analysis"
            and self._result.proposed_changes
        ):
            seen_paths: set[Path] = set()
            gaps: list[DocumentationGap] = []

            for change in self._result.proposed_changes:
                if change.document_path in seen_paths:
                    continue

                seen_paths.add(change.document_path)
                gaps.append(
                    DocumentationGap(
                        document_path=change.document_path,
                        section=change.section,
                        gap="Configured documentation gap.",
                        source_evidence=(
                            "Configured source function returns the "
                            "documented behavior."
                        ),
                        confidence=0.9,
                    )
                )

            return ReasoningResult(
                request_id=self._result.request_id,
                status=self._result.status,
                summary="Configured gap analysis.",
                impacts=(),
                proposed_changes=(),
                created_at=self._result.created_at,
                provider_name=self._result.provider_name,
                model_name=self._result.model_name,
                gaps=tuple(gaps),
                assumptions=self._result.assumptions,
                warnings=self._result.warnings,
                error_message=self._result.error_message,
                metadata=self._result.metadata,
            )

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


class StubSkillRegistry:
    """Return a configured local Agent Skill."""

    def __init__(
        self,
        skill: SkillDefinition | None = None,
        error: Exception | None = None,
    ) -> None:
        self._skill = skill
        self._error = error
        self.requests: list[str] = []

    def load(self, name: str) -> SkillDefinition:
        self.requests.append(name)

        if self._error is not None:
            raise self._error

        if self._skill is None:
            raise ValueError(f"Skill was not found: {name}")

        return self._skill


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
    skill_registry=None,
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
        skill_registry=skill_registry,
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
    assert reasoning_request.workflow_type == "documentation_gap_analysis"
    assert reasoning_request.target_paths == (Path("docs/index.md"),)
    assert reasoning_request.constraints == ()
    assert reasoning_request.skills == ()
    assert reasoning_request.metadata["workflow_id"] == "workflow-002"
    assert reasoning_request.metadata["documentation_stage"] == "gap_analysis"


def test_source_grounded_workflow_loads_strict_documentation_skill(
    tmp_path: Path,
) -> None:
    """Source-grounded reasoning receives the strict documentation skill."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path(
            "skills/strict-documentation-editor/SKILL.md"
        ),
        instructions="Apply the minimum textual modification.",
    )
    skill_registry = StubSkillRegistry(skill=skill)

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
        skill_registry=skill_registry,
    )
    workflow = components[0]
    reasoning_service = components[1]

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-strict-skill",
        )
    )

    assert skill_registry.requests == [
        "strict-documentation-editor",
    ]
    assert len(reasoning_service.requests) == 1
    assert reasoning_service.requests[0].workflow_type == (
        "documentation_gap_analysis"
    )
    assert reasoning_service.requests[0].skills == ()
    assert reasoning_service.requests[0].constraints == ()


def test_non_source_grounded_workflow_does_not_load_skill(
    tmp_path: Path,
) -> None:
    """Ordinary documentation reasoning preserves no-skill behavior."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path(
            "skills/strict-documentation-editor/SKILL.md"
        ),
        instructions="Apply the minimum textual modification.",
    )
    skill_registry = StubSkillRegistry(skill=skill)

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
        skill_registry=skill_registry,
    )
    workflow = components[0]
    reasoning_service = components[1]

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Review documentation.",
            target_paths=("docs/index.md",),
            workflow_id="workflow-no-strict-skill",
        )
    )

    assert skill_registry.requests == []
    assert reasoning_service.requests[0].skills == ()


def test_source_grounded_missing_strict_skill_fails_workflow(
    tmp_path: Path,
) -> None:
    """A configured source-grounded workflow fails closed if skill loading fails."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    skill_registry = StubSkillRegistry(
        error=ValueError(
            "Skill was not found: strict-documentation-editor"
        )
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
        skill_registry=skill_registry,
    )
    workflow = components[0]
    reasoning_service = components[1]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-missing-strict-skill",
        )
    )

    assert result.status is DocumentationWorkflowStatus.FAILED
    assert result.error_message == (
        "Skill was not found: strict-documentation-editor"
    )
    assert reasoning_service.requests == []
    assert validation_service.requests == []


def test_reasoning_result_debug_logging_preserves_structured_fields(
    tmp_path: Path,
    caplog,
) -> None:
    """Completed reasoning output is visible in DEBUG logs before filtering."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing behavior.",
        documentation_meaning="Existing behavior is documented.",
        proposed_content="Existing behavior is documented.",
        section=None,
        anchor_text="# Original",
        edit_type=DocumentationEditType.INSERT,
        confidence=0.85,
    )

    reasoning_result = _reasoning_result(
        proposed_changes=(change,),
        warnings=("Reasoning warning.",),
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=reasoning_result,
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
    )[0]

    with caplog.at_level(
        "DEBUG",
        logger="project0.workflow.documentation_workflow",
    ):
        workflow.execute(
            DocumentationWorkflowRequest(
                user_request="Update documentation.",
                target_paths=("docs/index.md",),
                workflow_id="workflow-reasoning-debug-log",
            )
        )

    assert "Documentation gap analysis result" not in caplog.text
    assert "Documentation proposal generation result summary='Reasoning summary.'" in (
        caplog.text
    )
    assert "warnings=('Reasoning warning.',)" in caplog.text
    assert "Documentation proposal generation proposed_change[1]" in caplog.text
    assert "document_path='docs/index.md'" in caplog.text
    assert "operation='update'" in caplog.text
    assert "rationale='Document existing behavior.'" in caplog.text
    assert (
        "documentation_meaning='Existing behavior is documented.'"
        in caplog.text
    )
    assert (
        "proposed_content='Existing behavior is documented.'"
        in caplog.text
    )
    assert "section=None" in caplog.text
    assert "anchor_text='# Original'" in caplog.text
    assert "edit_type='insert'" in caplog.text
    assert "confidence=0.85" in caplog.text


def test_source_grounded_workflow_runs_gap_analysis_before_edit_generation(
    tmp_path: Path,
) -> None:
    """Strict source-grounded work uses separate analysis and edit calls."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path("skills/strict-documentation-editor/SKILL.md"),
        instructions="Apply the minimum textual modification.",
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    proposed_content="Current documented behavior.",
                ),
            )
        ),
        validation_results=(
            _validation_result(ValidationStatus.PASSED),
        ),
        skill_registry=StubSkillRegistry(skill=skill),
    )
    workflow = components[0]
    reasoning_service = components[1]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-two-stage",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(reasoning_service.requests) == 2

    gap_request, edit_request = reasoning_service.requests

    assert gap_request.workflow_type == "documentation_gap_analysis"
    assert gap_request.skills == ()
    assert gap_request.metadata["documentation_stage"] == "gap_analysis"

    assert edit_request.workflow_type == "documentation_update"
    assert edit_request.skills == (skill,)
    assert edit_request.metadata["documentation_stage"] == (
        "proposal_generation"
    )
    assert "=== ESTABLISHED DOCUMENTATION GAPS ===" in edit_request.context
    assert "Configured documentation gap." in edit_request.context
    assert "Configured source function returns the documented behavior." in (
        edit_request.context
    )
    assert "Section: null" in edit_request.context
    assert (
        "Generate documentation edits only for the established gaps above."
        in edit_request.context
    )


def test_claim_level_gap_context_pairs_strong_claim_with_functions() -> None:
    """Stage 1 pairs exact prose with strongly matching source functions."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "# Example\n"
        "## Browser routes\n"
        "Path fields are trimmed; route parsing does not guarantee "
        "normalization or deduplication.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "def _parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(\n"
        "        line.strip() for line in value.splitlines() if line.strip()\n"
        "    ))\n"
        "\n"
        "def _parse_target_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(\n"
        "        line.strip() for line in value.splitlines() if line.strip()\n"
        "    ))\n"
        "\n"
        "def unrelated_request(value: str) -> str:\n"
        "    return value\n"
    )

    result = DocumentationWorkflow._build_claim_level_gap_context(
        context
    )

    assert "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===" in result
    assert "Pair 1:" in result
    assert "Section: Browser routes" in result
    assert (
        "Target Claim: Path fields are trimmed; route parsing does not "
        "guarantee normalization or deduplication."
        in result
    )
    assert "Function: _parse_source_paths" in result
    assert "Function: _parse_target_paths" in result
    assert "Function: unrelated_request" not in result
    assert result.count("Function: ") == 2


def test_claim_level_gap_context_excludes_classes_and_caps_function_snippet() -> None:
    """Pair context emits bounded functions, never complete class bodies."""

    long_body = "".join(
        f"        value_{index} = {index}\n"
        for index in range(30)
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "# Example\n"
        "## Parsing\n"
        "Source path parsing trims source path values.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "class Parser:\n"
        "    def parse_source_paths(self, value: str) -> tuple[str, ...]:\n"
        + long_body
        + "        return (value.strip(),)\n"
        "\n"
        "    def unrelated_method(self) -> None:\n"
        "        pass\n"
    )

    result = DocumentationWorkflow._build_claim_level_gap_context(
        context
    )

    assert "class Parser:" not in result
    assert "Function: parse_source_paths" in result
    assert "# ... snippet truncated ..." in result
    assert "value_29 = 29" not in result
    assert "Function: unrelated_method" not in result


def test_claim_level_gap_context_limits_pairs_to_four() -> None:
    """Stage 1 pairing is capped at four strongest claim pairs."""

    target_claims = "".join(
        (
            f"## Section {index}\n"
            f"Parse source path {index} uses parse source paths.\n"
        )
        for index in range(6)
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "# Example\n"
        + target_claims
        + "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "def parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return (value.strip(),)\n"
    )

    result = DocumentationWorkflow._build_claim_level_gap_context(
        context
    )

    assert result.count("Pair ") == 4


def test_claim_level_gap_context_falls_back_without_strong_function_match() -> None:
    """Existing claim-candidate behavior remains when no strong pair exists."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "# Example\n"
        "## Contract\n"
        "Documented behavior.\n"
        "```python\n"
        "internal_call()\n"
        "```\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "def unrelated(value: int) -> int:\n"
        "    return value + 1\n"
    )

    result = DocumentationWorkflow._build_claim_level_gap_context(
        context
    )
    candidate_block = result.split(
        "=== TARGET DOCUMENTATION CLAIM CANDIDATES ===",
        1,
    )[1]

    assert "Text: Documented behavior." in candidate_block
    assert "internal_call()" not in candidate_block
    assert "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===" not in result


def test_source_grounded_gap_request_uses_bounded_pair_context(
    tmp_path: Path,
) -> None:
    """Source-grounded Stage 1 receives only bounded strong claim pairs."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Contract\n"
        "Route path parsing does not guarantee deduplication.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "def parse_route_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
        "\n"
        "def unrelated() -> None:\n"
        "    pass\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
        context_provider=context_provider,
    )
    workflow = components[0]
    reasoning_service = components[1]

    workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-bounded-gap-context",
        )
    )

    assert len(reasoning_service.requests) == 1
    gap_request = reasoning_service.requests[0]
    assert gap_request.workflow_type == "documentation_gap_analysis"
    assert "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===" in (
        gap_request.context
    )
    assert (
        "Target Claim: Route path parsing does not guarantee deduplication."
        in gap_request.context
    )
    assert "Function: parse_route_paths" in gap_request.context
    assert "def unrelated" not in gap_request.context


def test_split_bounded_gap_context_creates_one_context_per_pair() -> None:
    """Each bounded pair becomes an independent Stage 1 request context."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "First claim.\n"
        "Second claim.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Evaluate pairs.\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: First claim.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_first\n"
        "def parse_first(value: str) -> str:\n"
        "    return value.strip()\n"
        "Pair 2:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Second claim.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_second\n"
        "def parse_second(value: str) -> str:\n"
        "    return value\n"
    )

    contexts = DocumentationWorkflow._split_bounded_gap_context(context)

    assert len(contexts) == 2
    assert "Target Claim: First claim." in contexts[0]
    assert "Function: parse_first" in contexts[0]
    assert "Target Claim: Second claim." not in contexts[0]
    assert "Function: parse_second" not in contexts[0]
    assert "Target Claim: Second claim." in contexts[1]
    assert "Function: parse_second" in contexts[1]


def test_gap_source_evidence_rejects_path_only_and_accepts_behavior() -> None:
    """Stage 1 path-only evidence fails closed."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "Route parsing does not guarantee deduplication.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Route parsing does not guarantee deduplication.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_route_paths\n"
        "def parse_route_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
    )
    path_only = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap="The target incorrectly denies deduplication.",
        source_evidence="src/project0/example.py",
        confidence=0.9,
    )
    substantive = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap="The target incorrectly denies deduplication.",
        source_evidence=(
            "parse_route_paths returns tuple(dict.fromkeys(...)), "
            "which removes duplicate path values."
        ),
        confidence=0.9,
    )

    assert not DocumentationWorkflow._gap_has_substantive_source_evidence(
        gap=path_only,
        gap_context=context,
    )
    assert DocumentationWorkflow._gap_has_substantive_source_evidence(
        gap=substantive,
        gap_context=context,
    )



def test_gap_rejection_reason_rejects_absence_based_contradiction() -> None:
    """Missing paired evidence cannot establish a documentation gap."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Reasoning and validation\n"
        "The default validation interface runs Markdown, Link, and MkDocs "
        "validators.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Reasoning and validation\n"
        "Target Claim: The default validation interface runs Markdown, "
        "Link, and MkDocs validators.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_source_paths\n"
        "def parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return (value,)\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Reasoning and validation",
        gap=(
            "The claim is unsupported because there is no evidence in the "
            "paired source snippets."
        ),
        source_evidence=(
            "src/project0/example.py does not provide evidence for the "
            "validator claim."
        ),
        confidence=0.95,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == "absence of evidence was treated as contradiction"


def test_gap_rejection_reason_rejects_exact_target_claim_as_gap() -> None:
    """A model cannot return the target claim itself as a discrepancy."""

    claim = (
        "| `POST` | `/agents/documentation/request` | Request and optional "
        "source/target paths | Run the synchronous workflow and render current "
        "state. |"
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        f"{claim}\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        f"Target Claim: {claim}\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_source_paths\n"
        "def parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=claim,
        source_evidence=(
            "parse_source_paths deduplicates newline-separated path values "
            "using dict.fromkeys."
        ),
        confidence=0.9,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == "gap merely repeated the target claim"



def test_gap_rejection_reason_rejects_substantial_target_claim_subset() -> None:
    """A substantial contiguous target sentence is not a new gap."""

    claim = (
        "The default validation interface runs Markdown, Link, and MkDocs "
        "validators; Documentation Consistency Validator is separate. "
        "The shared reasoning abstraction requires schema-constrained "
        "structured gap or update objects."
    )
    repeated = (
        "The default validation interface runs Markdown, Link, and MkDocs "
        "validators Documentation Consistency Validator is separate"
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Reasoning and validation\n"
        f"{claim}\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Reasoning and validation\n"
        f"Target Claim: {claim}\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_source_paths\n"
        "def parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return (value,)\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Reasoning and validation",
        gap=repeated,
        source_evidence=(
            "parse_source_paths returns parsed path values from the request."
        ),
        confidence=0.9,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == "gap merely repeated the target claim"


def test_gap_repetition_guard_preserves_short_quoted_contradiction() -> None:
    """Quoting a few target words inside a real contradiction is allowed."""

    claim = (
        "Route parsing does not guarantee normalization or deduplication."
    )
    gap_text = (
        "The target says route parsing does not guarantee deduplication, "
        "but parse_route_paths deduplicates values with dict.fromkeys."
    )

    assert not DocumentationWorkflow._gap_repeats_target_claim(
        gap_text=gap_text,
        target_claim=claim,
    )



def test_gap_rejection_reason_rejects_missing_paired_function_name() -> None:
    """Implementation helper names are not required target documentation."""

    claim = (
        "| `POST` | `/agents/documentation/request` | Request and optional "
        "source/target paths | Run the synchronous workflow and render current "
        "state. |"
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        f"{claim}\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        f"Target Claim: {claim}\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: _parse_target_paths\n"
        "def _parse_target_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "The target documentation does not mention the "
            "`_parse_target_paths` function, which is present in source."
        ),
        source_evidence=(
            "_parse_target_paths converts newline-separated target paths "
            "into normalized values."
        ),
        confidence=0.95,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == (
        "gap treated a paired implementation helper name as required documentation"
    )


def test_gap_repetition_guard_rejects_long_sentence_from_larger_claim() -> None:
    """A long existing sentence is rejected even inside a larger paragraph."""

    claim = (
        "The default validation interface runs Markdown, Link, and MkDocs "
        "validators; Documentation Consistency Validator is separate. "
        "Preliminary validation checks distinct accepted-proposal paths "
        "before review; final validation checks successfully applied paths."
    )
    repeated = (
        "The default validation interface runs Markdown Link and MkDocs "
        "validators Documentation Consistency Validator is separate"
    )

    assert DocumentationWorkflow._gap_repeats_target_claim(
        gap_text=repeated,
        target_claim=claim,
    )


def test_gap_rejection_reason_rejects_missing_term_present_in_target() -> None:
    """An omission gap fails when the exact target claim already has the term."""

    claim = (
        "| `POST` | `/agents/documentation/review` | Workflow ID, proposal "
        "ID, decision, optional feedback | Submit one decision and render "
        "updated state. |"
    )
    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        f"{claim}\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        f"Target Claim: {claim}\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: documentation_agent_submit_review\n"
        "async def documentation_agent_submit_review(\n"
        "    feedback: str = Form(\"\"),\n"
        ") -> HTMLResponse:\n"
        "    ...\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "The target documentation does not mention the `feedback` "
            "parameter in the request."
        ),
        source_evidence=(
            "documentation_agent_submit_review accepts feedback as an "
            "optional form field."
        ),
        confidence=1.0,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == "gap claimed an omission already present in the target claim"


def test_gap_rejection_reason_preserves_positive_source_contradiction() -> None:
    """Concrete positive contradiction remains eligible for Stage 2."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "Path fields are newline-separated and trimmed; route parsing does "
        "not guarantee deduplication.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Path fields are newline-separated and trimmed; route "
        "parsing does not guarantee deduplication.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_source_paths\n"
        "def parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "The target says route parsing does not guarantee "
            "deduplication, but parse_source_paths deduplicates values."
        ),
        source_evidence=(
            "parse_source_paths returns tuple(dict.fromkeys(...)), removing "
            "duplicate path values."
        ),
        confidence=0.95,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) is None



def test_gap_rejection_reason_rejects_reversed_deduplication_polarity() -> None:
    """A negative gap cannot contradict deterministic positive source behavior."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "Path fields are newline-separated, trimmed, and stripped of blank "
        "entries; route parsing does not guarantee normalization or "
        "deduplication.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Path fields are newline-separated, trimmed, and stripped "
        "of blank entries; route parsing does not guarantee normalization or "
        "deduplication.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: _parse_source_paths\n"
        "def _parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(\n"
        "        dict.fromkeys(\n"
        "            line.strip()\n"
        "            for line in value.splitlines()\n"
        "            if line.strip()\n"
        "        )\n"
        "    )\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "_parse_source_paths does not guarantee normalization or "
            "deduplication of parsed paths."
        ),
        source_evidence=(
            "_parse_source_paths uses line.strip() and dict.fromkeys(...) "
            "when returning parsed path values."
        ),
        confidence=1.0,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) == "gap reversed positive authoritative source behavior"


def test_gap_rejection_reason_preserves_correct_deduplication_polarity() -> None:
    """A correctly stated source contradiction remains eligible."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "Route parsing does not guarantee deduplication.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Route parsing does not guarantee deduplication.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: parse_route_paths\n"
        "def parse_route_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "The target incorrectly says route parsing does not guarantee "
            "deduplication; parse_route_paths deduplicates values."
        ),
        source_evidence=(
            "parse_route_paths returns tuple(dict.fromkeys(...)), removing "
            "duplicate path values."
        ),
        confidence=0.98,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) is None



def test_polarity_guard_is_clause_local_for_source_function() -> None:
    """Later negative wording about the target must not taint source polarity."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/Example.md\n"
        "## Browser routes\n"
        "Route parsing does not guarantee normalization or deduplication.\n"
        "\n"
        "=== BOUNDED TARGET-SOURCE CLAIM PAIRS ===\n"
        "Pair 1:\n"
        "Document Path: docs/Example.md\n"
        "Section: Browser routes\n"
        "Target Claim: Route parsing does not guarantee normalization or "
        "deduplication.\n"
        "Paired Authoritative Source:\n"
        "Path: src/project0/example.py\n"
        "Function: _parse_source_paths\n"
        "def _parse_source_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(line.strip() for line in value.splitlines()))\n"
    )
    gap = DocumentationGap(
        document_path=Path("docs/Example.md"),
        section="Browser routes",
        gap=(
            "_parse_source_paths guarantees normalization and deduplication "
            "of path parsing, which contradicts the target claim that route "
            "parsing does not guarantee these properties."
        ),
        source_evidence=(
            "_parse_source_paths uses line.strip() and dict.fromkeys(...) "
            "when returning parsed path values."
        ),
        confidence=0.95,
    )

    assert DocumentationWorkflow._documentation_gap_rejection_reason(
        gap=gap,
        gap_context=context,
    ) is None


def test_positive_source_behavior_inference_is_narrow() -> None:
    """Only deterministic syntax currently recognized by strict mode is inferred."""

    source = (
        "def parse_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(\n"
        "        dict.fromkeys(\n"
        "            line.strip()\n"
        "            for line in value.splitlines()\n"
        "            if line.strip()\n"
        "        )\n"
        "    )\n"
    )

    behaviors = DocumentationWorkflow._infer_positive_source_behaviors(source)

    assert "deduplication" in behaviors
    assert "deduplicate" in behaviors
    assert "normalization" in behaviors
    assert "trim" in behaviors
    assert "blank-removal" in behaviors
    assert "validation" not in behaviors


def test_source_grounded_workflow_verifies_bounded_pairs_independently(
    tmp_path: Path,
) -> None:
    """Pair-level Stage 1 rejects path-only gaps and preserves valid ones."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Contract\n"
        "Route path parsing does not guarantee deduplication.\n"
        "Review submission accepts a decision.\n",
        encoding="utf-8",
    )

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Contract\n"
        "Route path parsing does not guarantee deduplication.\n"
        "Review submission accepts a decision.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "def parse_route_paths(value: str) -> tuple[str, ...]:\n"
        "    return tuple(dict.fromkeys(value.splitlines()))\n"
        "\n"
        "def submit_review_decision(decision: str) -> str:\n"
        "    return decision\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    class PairReasoningService:
        def __init__(self) -> None:
            self.requests: list[ReasoningRequest] = []

        def reason(self, request: ReasoningRequest) -> ReasoningResult:
            self.requests.append(request)

            if request.workflow_type == "documentation_gap_analysis":
                if "parse_route_paths" in request.context:
                    gap = DocumentationGap(
                        document_path=Path("docs/index.md"),
                        section="Contract",
                        gap=(
                            "The target says route parsing does not guarantee "
                            "deduplication, but the source deduplicates values."
                        ),
                        source_evidence=(
                            "parse_route_paths returns "
                            "tuple(dict.fromkeys(...)), removing duplicate "
                            "path values."
                        ),
                        confidence=0.95,
                    )
                else:
                    gap = DocumentationGap(
                        document_path=Path("docs/index.md"),
                        section="Contract",
                        gap="Review submission is incomplete.",
                        source_evidence="src/project0/example.py",
                        confidence=0.7,
                    )

                return ReasoningResult(
                    request_id="pair-gap",
                    status=ReasoningStatus.COMPLETED,
                    summary="Pair checked.",
                    impacts=(),
                    proposed_changes=(),
                    created_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
                    provider_name="stub",
                    model_name="stub-model",
                    gaps=(gap,),
                )

            return ReasoningResult(
                request_id="proposal",
                status=ReasoningStatus.COMPLETED,
                summary="No proposal.",
                impacts=(),
                proposed_changes=(),
                created_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
                provider_name="stub",
                model_name="stub-model",
            )

    reasoning_service = PairReasoningService()
    workflow = DocumentationWorkflow(
        repository_root=tmp_path,
        context_provider=context_provider,
        reasoning_service=reasoning_service,
        artifact_location_service=StubArtifactLocationService(),
        validation_service=StubValidationService(()),
        review_coordinator=StubReviewCoordinator(),
        repository_update_service=StubRepositoryUpdateService(),
        git_diff_service=StubGitDiffService(),
    )

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-pair-verification",
        )
    )

    gap_requests = tuple(
        request
        for request in reasoning_service.requests
        if request.workflow_type == "documentation_gap_analysis"
    )

    assert len(gap_requests) == 2
    assert all(
        request.metadata["gap_pair_count"] == 2
        for request in gap_requests
    )
    assert gap_requests[0].metadata["gap_pair_index"] == 1
    assert gap_requests[1].metadata["gap_pair_index"] == 2
    assert result.reasoning_result is not None

    edit_requests = tuple(
        request
        for request in reasoning_service.requests
        if request.workflow_type == "documentation_update"
    )
    assert len(edit_requests) == 1
    assert (
        "parse_route_paths returns tuple(dict.fromkeys(...)), "
        "removing duplicate path values."
        in edit_requests[0].context
    )
    assert "Review submission is incomplete." not in edit_requests[0].context


def test_documentation_gap_deduplication_preserves_first_exact_gap() -> None:
    """Exact Stage 1 duplicates are removed before proposal generation."""

    first = DocumentationGap(
        document_path=Path("docs/index.md"),
        section="Interface Contract",
        gap="The documented contract omits context input.",
        source_evidence="The execute signature accepts context_content.",
        confidence=0.9,
    )
    duplicate = DocumentationGap(
        document_path=Path("docs/index.md"),
        section="Interface Contract",
        gap="The documented contract omits   context input.",
        source_evidence="The execute signature accepts context_content.",
        confidence=0.8,
    )

    result = DocumentationWorkflow._deduplicate_documentation_gaps(
        (first, duplicate)
    )

    assert result == (first,)


def test_source_grounded_workflow_stops_after_gap_analysis_when_no_gaps(
    tmp_path: Path,
) -> None:
    """No Stage 1 gaps means no Stage 2 proposal-generation call."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(),
        validation_results=(),
    )
    workflow = components[0]
    reasoning_service = components[1]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-two-stage-no-gaps",
        )
    )

    assert len(reasoning_service.requests) == 1
    assert reasoning_service.requests[0].workflow_type == (
        "documentation_gap_analysis"
    )
    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []


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


def test_source_grounded_meta_instruction_content_is_skipped(
    tmp_path: Path,
) -> None:
    """Instructional prose is not surfaced as documentation content."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Per-Paper Analysis Interface Contract\n"
        "Existing details.\n",
        encoding="utf-8",
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                ProposedDocumentationChange(
                    document_path=Path("docs/index.md"),
                    operation=DocumentationChangeOperation.UPDATE,
                    rationale="Reflect current shared research models.",
                    proposed_content=(
                        "Add sections for each of the defined classes, "
                        "explaining their purpose and attributes. Include "
                        "examples of how they might be used."
                    ),
                    section="Per-Paper Analysis Interface Contract",
                    anchor_text=None,
                    edit_type=DocumentationEditType.REPLACE,
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
            workflow_id="workflow-meta-instruction",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "described what should be written instead of providing concrete Markdown"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_consider_adding_recommendation_is_skipped(
    tmp_path: Path,
) -> None:
    """Implementation recommendations are not surfaced for strict review."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Research Source Provider Interface Contract\n"
        "Existing details.\n",
        encoding="utf-8",
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                ProposedDocumentationChange(
                    document_path=Path("docs/index.md"),
                    operation=DocumentationChangeOperation.UPDATE,
                    rationale=(
                        "The current model lacks a clear mechanism for "
                        "handling conflicting evidence or uncertainties."
                    ),
                    proposed_content=(
                        "Consider adding a `confidence_score` field to "
                        "`ResearchFinding` and `ResearchDirection`."
                    ),
                    section="Research Source Provider Interface Contract",
                    anchor_text=None,
                    edit_type=DocumentationEditType.REPLACE,
                ),
            )
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-consider-adding-recommendation",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "described what should be written instead of providing concrete Markdown"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_meta_instruction_rejection_logs_content(
    tmp_path: Path,
    caplog,
) -> None:
    """Rejected source-grounded meta instructions are visible in DEBUG logs."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Interfaces\n"
        "Existing details.\n",
        encoding="utf-8",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Reflect current interfaces.",
        proposed_content=(
            "Add documentation describing the current interfaces."
        ),
        section="Interfaces",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(),
    )[0]

    with caplog.at_level(
        "DEBUG",
        logger="project0.workflow.documentation_workflow",
    ):
        workflow.execute(
            DocumentationWorkflowRequest(
                user_request="Update documentation.",
                target_paths=("docs/index.md",),
                source_paths=("src/project0/example.py",),
                workflow_id="workflow-meta-instruction-log",
            )
        )

    assert (
        "Rejected source-grounded meta-instruction content for "
        "docs/index.md: 'Add documentation describing the current "
        "interfaces.'"
        in caplog.text
    )


def test_source_grounded_python_declaration_is_canonicalized(
    tmp_path: Path,
) -> None:
    """A uniquely matched source declaration replaces model-normalized code."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "```python\n"
        "existing_call()\n"
        "```\n",
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

    authoritative_declaration = (
        "def execute(\n"
        "    self,\n"
        "    request: ResearchRequest,\n"
        "    context_source_name: str | None = None,\n"
        "    context_content: bytes | None = None,\n"
        ") -> ResearchResult:\n"
        "    \"\"\"Execute the research workflow.\"\"\"\n"
        "\n"
        "    ..."
    )

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/interfaces/research_interfaces.py\n"
        "class ResearchWorkflowProtocol:\n"
        + "\n".join(
            f"    {line}" if line else line
            for line in authoritative_declaration.splitlines()
        )
        + "\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            "def execute(\n"
            "    self,\n"
            "    request: ResearchRequest,\n"
            "    context_source_name: str | None = None,\n"
            "    context_content: bytes | None = None,\n"
            ") -> ResearchResult:\n"
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
        context_provider=context_provider,
        artifact_locations=(location,),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=(
                "src/project0/interfaces/research_interfaces.py",
            ),
            workflow_id="workflow-source-code-canonicalized",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert result.proposals[0].proposed_content == (
        "```python\n"
        f"{authoritative_declaration}\n"
        "```"
    )
    assert not any(
        "did not exactly match an authoritative source declaration"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_python_declaration_mismatch_logs_comparison(
    tmp_path: Path,
    caplog,
) -> None:
    """Rejected Python declarations log proposed and authoritative text."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "```python\n"
        "existing_call()\n"
        "```\n",
        encoding="utf-8",
    )

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/interfaces/research_interfaces.py\n"
        "class ResearchWorkflowProtocol:\n"
        "    def execute(\n"
        "        self,\n"
        "        request: ResearchRequest,\n"
        "    ) -> ResearchResult:\n"
        "        \"\"\"Execute the research workflow.\"\"\"\n"
        "        ...\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document the workflow interface.",
        proposed_content=(
            "```python\n"
            "def execute(\n"
            "    self,\n"
            "    request: ResearchRequest,\n"
            "    unsupported: str = \"\",\n"
            ") -> ResearchResult:\n"
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
        validation_results=(),
        context_provider=context_provider,
    )[0]

    with caplog.at_level(
        "DEBUG",
        logger="project0.workflow.documentation_workflow",
    ):
        workflow.execute(
            DocumentationWorkflowRequest(
                user_request="Update documentation.",
                target_paths=("docs/index.md",),
                source_paths=(
                    "src/project0/interfaces/research_interfaces.py",
                ),
                workflow_id="workflow-source-code-mismatch-log",
            )
        )

    assert (
        "Rejected source-grounded Python declaration for docs/index.md"
        in caplog.text
    )
    assert "proposed_declarations=" in caplog.text
    assert "authoritative_declarations=" in caplog.text
    assert "pass" in caplog.text
    assert "Execute the research workflow." in caplog.text
    assert "..." in caplog.text


def test_source_grounded_python_canonicalization_requires_unique_match() -> None:
    """Ambiguous authoritative signatures are not canonicalized."""

    proposed_content = (
        "```python\n"
        "def execute(self, request: ResearchRequest) -> ResearchResult:\n"
        "    pass\n"
        "```"
    )
    context = (
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/first.py\n"
        "class FirstProtocol:\n"
        "    def execute(self, request: ResearchRequest) -> ResearchResult:\n"
        "        \"\"\"First implementation contract.\"\"\"\n"
        "        ...\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/second.py\n"
        "class SecondProtocol:\n"
        "    def execute(self, request: ResearchRequest) -> ResearchResult:\n"
        "        \"\"\"Second implementation contract.\"\"\"\n"
        "        ...\n"
    )

    canonicalized = DocumentationWorkflow._canonicalize_python_declarations(
        proposed_content=proposed_content,
        context=context,
    )

    assert canonicalized == proposed_content
    assert not DocumentationWorkflow._python_declarations_are_source_grounded(
        proposed_content=canonicalized,
        context=context,
    )


def test_source_grounded_exact_python_declaration_is_reviewable(
    tmp_path: Path,
) -> None:
    """Exact authoritative Python declarations remain reviewable."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "```python\n"
        "existing_call()\n"
        "```\n",
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

    declaration = (
        "def execute(\n"
        "    self,\n"
        "    request: ResearchRequest,\n"
        "    context_source_name: str | None = None,\n"
        "    context_content: bytes | None = None,\n"
        ") -> ResearchResult:\n"
        "    \"\"\"Execute the research workflow.\"\"\"\n"
        "    ..."
    )

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing details.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/interfaces/research_interfaces.py\n"
        "class ResearchWorkflowProtocol:\n"
        + "\n".join(
            f"    {line}" if line else line
            for line in declaration.splitlines()
        )
        + "\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            f"{declaration}\n"
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
        context_provider=context_provider,
        artifact_locations=(location,),
    )[0]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Update documentation.",
            target_paths=("docs/index.md",),
            source_paths=(
                "src/project0/interfaces/research_interfaces.py",
            ),
            workflow_id="workflow-source-code-exact",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert not any(
        "did not exactly match an authoritative source declaration"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_python_block_uses_documentation_meaning(
    tmp_path: Path,
) -> None:
    """Prose meaning replaces fenced Python in a prose-only target section."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing prose details.\n",
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
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            "def execute(self) -> None:\n"
            "    ...\n"
            "```"
        ),
        documentation_meaning=(
            "The workflow accepts optional existing research context "
            "content for analysis."
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
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-python-meaning-fallback",
        )
    )

    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert len(result.proposals) == 1
    assert result.proposals[0].proposed_content == (
        "The workflow accepts optional existing research context "
        "content for analysis."
    )
    assert not any(
        "does not already use fenced Python content"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_python_block_logs_documentation_meaning(
    tmp_path: Path,
    caplog,
) -> None:
    """Source-grounded fallback evaluation logs the returned meaning."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing prose details.\n",
        encoding="utf-8",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            "def execute(self) -> None:\n"
            "    ...\n"
            "```"
        ),
        documentation_meaning=(
            "This change will ensure that provided context can be used."
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
        validation_results=(),
    )[0]

    with caplog.at_level(
        "DEBUG",
        logger="project0.workflow.documentation_workflow",
    ):
        workflow.execute(
            DocumentationWorkflowRequest(
                user_request="Synchronize documentation.",
                target_paths=("docs/index.md",),
                source_paths=("src/project0/example.py",),
                workflow_id="workflow-python-meaning-log",
            )
        )

    assert (
        "Evaluating source-grounded documentation meaning fallback for "
        "docs/index.md: 'This change will ensure that provided context "
        "can be used.'"
        in caplog.text
    )


def test_source_grounded_python_block_rejects_rationale_like_meaning(
    tmp_path: Path,
) -> None:
    """Rationale-like fallback prose is not surfaced as documentation."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing prose details.\n",
        encoding="utf-8",
    )

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            "def execute(self) -> None:\n"
            "    ...\n"
            "```"
        ),
        documentation_meaning=(
            "This change will ensure that the Research Agent can "
            "incorporate provided context into its analysis."
        ),
        section="Existing Research Context Interface Contract",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(),
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=("src/project0/example.py",),
            workflow_id="workflow-python-rationale-meaning",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "does not already use fenced Python content"
        in warning
        for warning in result.warnings
    )


def test_source_grounded_new_python_block_without_target_form_is_skipped(
    tmp_path: Path,
) -> None:
    """New fenced Python is rejected when the target section uses prose."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing prose details.\n",
        encoding="utf-8",
    )

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing prose details.\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/interfaces/research_interfaces.py\n"
        "class ResearchWorkflowProtocol:\n"
        "    def execute(self) -> None:\n"
        "        ...\n"
    )

    def context_provider(
        request: DocumentationWorkflowRequest,
    ) -> str:
        del request
        return context

    change = ProposedDocumentationChange(
        document_path=Path("docs/index.md"),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document existing research context handling.",
        proposed_content=(
            "```python\n"
            "def execute(self) -> None:\n"
            "    ...\n"
            "```"
        ),
        documentation_meaning=None,
        section="Existing Research Context Interface Contract",
        anchor_text=None,
        edit_type=DocumentationEditType.REPLACE,
    )

    components = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(change,)
        ),
        validation_results=(),
        context_provider=context_provider,
    )
    workflow = components[0]
    validation_service = components[2]

    result = workflow.execute(
        DocumentationWorkflowRequest(
            user_request="Synchronize documentation.",
            target_paths=("docs/index.md",),
            source_paths=(
                "src/project0/interfaces/research_interfaces.py",
            ),
            workflow_id="workflow-python-target-form",
        )
    )

    assert result.proposals == ()
    assert result.preliminary_validation is None
    assert validation_service.requests == []
    assert any(
        "does not already use fenced Python content"
        in warning
        for warning in result.warnings
    )


def test_python_target_form_guard_allows_existing_section_python() -> None:
    """Existing fenced Python in the affected section permits code updates."""

    original_content = (
        "# Original\n"
        "## Interface Contract\n"
        "```python\n"
        "existing_call()\n"
        "```\n"
        "## Other\n"
        "Other details.\n"
    )

    assert not (
        DocumentationWorkflow._introduces_python_fence_without_target_form(
            original_content=original_content,
            proposed_content=(
                "```python\n"
                "updated_call()\n"
                "```"
            ),
            section="Interface Contract",
        )
    )
    assert (
        DocumentationWorkflow._introduces_python_fence_without_target_form(
            original_content=original_content,
            proposed_content=(
                "```python\n"
                "updated_call()\n"
                "```"
            ),
            section="Other",
        )
    )


def test_source_grounded_non_declaration_python_example_preserves_behavior(
    tmp_path: Path,
) -> None:
    """Python examples that do not declare source interfaces are unaffected."""

    context = (
        "=== TARGET DOCUMENTATION ===\n"
        "Path: docs/index.md\n"
        "# Original\n"
        "\n"
        "=== AUTHORITATIVE SOURCE ===\n"
        "Path: src/project0/example.py\n"
        "VALUE = 1\n"
    )

    assert DocumentationWorkflow._python_declarations_are_source_grounded(
        proposed_content=(
            "```python\n"
            "request = ResearchRequest(question=\"example\")\n"
            "```"
        ),
        context=context,
    )


def test_non_source_grounded_meta_instruction_remains_reviewable(
    tmp_path: Path,
) -> None:
    """Ordinary documentation requests preserve legacy model behavior."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text("# Original\n", encoding="utf-8")

    workflow = _create_workflow(
        tmp_path,
        reasoning_result=_reasoning_result(
            proposed_changes=(
                _update_change(
                    proposed_content="Add documentation for the new model.",
                    anchor_text="# Original",
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
            workflow_id="workflow-non-source-meta",
        )
    )

    assert len(result.proposals) == 1


def test_meta_instruction_detector_allows_concrete_markdown() -> None:
    """Concrete Markdown beginning with structure is not rejected."""

    assert not DocumentationWorkflow._is_meta_instruction_content(
        "## Model Contract\n\nDescribe the model's exported fields."
    )
    assert not DocumentationWorkflow._is_meta_instruction_content(
        "- Includes source identifiers."
    )
    assert not DocumentationWorkflow._is_meta_instruction_content(
        "```python\nclass Example:\n    pass\n```"
    )


def test_documentation_meaning_quality_guard_rejects_change_rationale() -> None:
    """Fallback meaning must state current behavior, not change rationale."""

    rejected = (
        "This change will ensure that context can be incorporated.",
        "This update improves the documented workflow.",
        "This will make the interface more flexible.",
        "This ensures that existing context can be analyzed.",
    )

    accepted = (
        "The workflow accepts optional existing research context content.",
        "Existing research context can be incorporated into the analysis.",
    )

    assert all(
        DocumentationWorkflow._is_rationale_like_documentation_meaning(
            value
        )
        for value in rejected
    )
    assert all(
        not DocumentationWorkflow._is_rationale_like_documentation_meaning(
            value
        )
        for value in accepted
    )


def test_meta_instruction_detector_rejects_common_planning_phrases() -> None:
    """Common imperative planning prose is rejected."""

    examples = (
        "Add sections for each model.",
        "Consider adding a `confidence_score` field to `ResearchFinding`.",
        "Include examples of interface usage.",
        "Explain the responsibilities of each class.",
        "Describe the model relationships.",
        "Document the new interface.",
        "Update the documentation to reflect the model.",
    )

    assert all(
        DocumentationWorkflow._is_meta_instruction_content(value)
        for value in examples
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
            "Existing research context handling accepts a context source "
            "name and context content."
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

    proposal = result.proposals[0]

    assert proposal.anchor_mode is DocumentationAnchorMode.INSERT_AFTER
    assert proposal.artifact_location is not None
    assert (
        proposal.artifact_location.location_type
        is ArtifactLocationType.LINE_RANGE
    )
    assert proposal.artifact_location.locator == context_location.locator
    assert proposal.artifact_location.start_line == context_location.start_line
    assert proposal.artifact_location.end_line == context_location.start_line
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


def test_source_grounded_section_snippet_preserves_existing_section(
    tmp_path: Path,
) -> None:
    """A section-scoped snippet is converted to a localized insertion."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing context details.\n",
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
        rationale="Document existing research context handling.",
        proposed_content=(
            "The workflow accepts an optional context source name."
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
            workflow_id="workflow-safe-section-snippet",
        )
    )

    proposal = result.proposals[0]

    assert proposal.anchor_mode is DocumentationAnchorMode.INSERT_AFTER
    assert proposal.artifact_location is not None
    assert (
        proposal.artifact_location.location_type
        is ArtifactLocationType.LINE_RANGE
    )
    assert proposal.artifact_location.start_line == 2
    assert proposal.artifact_location.end_line == 2


def test_source_grounded_complete_section_replacement_remains_replace(
    tmp_path: Path,
) -> None:
    """A proposal containing the exact section heading may replace it."""

    document = tmp_path / "docs/index.md"
    document.parent.mkdir()
    document.write_text(
        "# Original\n"
        "## Existing Research Context Interface Contract\n"
        "Existing context details.\n",
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
        rationale="Replace the existing research context section.",
        proposed_content=(
            "## Existing Research Context Interface Contract\n"
            "Updated context details."
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
            workflow_id="workflow-full-section-replace",
        )
    )

    proposal = result.proposals[0]

    assert proposal.anchor_mode is DocumentationAnchorMode.REPLACE
    assert proposal.artifact_location == location


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
            "The workflow accepts an optional context source name."
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

    proposal = result.proposals[0]

    assert proposal.anchor_mode is DocumentationAnchorMode.INSERT_AFTER
    assert proposal.artifact_location is not None
    assert (
        proposal.artifact_location.location_type
        is ArtifactLocationType.LINE_RANGE
    )
    assert proposal.artifact_location.locator == location.locator
    assert proposal.artifact_location.start_line == location.start_line
    assert proposal.artifact_location.end_line == location.start_line
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
