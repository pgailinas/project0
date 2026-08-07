# ============================================================
# Project0 - Documentation Agent UI Service
#
# File: documentation_agent_ui_service.py
#
# Purpose:
#     Adapt Documentation Agent workflow results into browser-
#     facing view models used by the Dashboard interface.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from project0.agents.documentation.documentation_agent_view_models import (
    DifferenceLineType,
    DifferenceLineView,
    DocumentationAgentPageStatus,
    DocumentationAgentPageView,
    DocumentationDifferenceView,
    DocumentationProposalView,
    DocumentationRequestForm,
    DocumentationWorkflowSummaryView,
    ValidationDisplayStatus,
    ValidationMessageView,
    ValidationResultView,
)
from project0.models.documentation_workflow_models import ReviewDecision


class DocumentationWorkflowPort(Protocol):
    """Minimal workflow interface required by the UI service."""

    def execute(self, request: object) -> object:
        """Execute a documentation workflow request."""


class DocumentationReviewPort(Protocol):
    """Minimal review interface required by the UI service."""

    def submit_decision(
        self,
        workflow_id: str,
        proposal_id: str,
        decision: ReviewDecision,
        feedback: str | None = None,
    ) -> object:
        """Submit one user review decision."""


@dataclass(frozen=True, slots=True)
class DocumentationAgentUIService:
    """Coordinate Documentation Agent UI requests and presentation state."""

    workflow: DocumentationWorkflowPort
    review_service: DocumentationReviewPort | None = None

    def create_ready_page(self) -> DocumentationAgentPageView:
        """Create the initial Documentation Agent page state."""

        return DocumentationAgentPageView(
            page_status=DocumentationAgentPageStatus.READY,
            status_message="Ready for a documentation request.",
            request_form=DocumentationRequestForm(),
        )

    def submit_request(
        self,
        user_request: str,
        target_paths: Sequence[str] | None = None,
    ) -> DocumentationAgentPageView:
        """Submit a documentation request and return display-ready state."""

        request_form = self._build_request_form(
            user_request=user_request,
            target_paths=target_paths,
        )

        if not request_form.user_request:
            return DocumentationAgentPageView(
                page_status=DocumentationAgentPageStatus.FAILED,
                status_message="A documentation request is required.",
                request_form=request_form,
                error_message="Enter a documentation request before continuing.",
            )

        try:
            workflow_request = self._create_workflow_request(request_form)
            workflow_result = self.workflow.execute(workflow_request)
        except Exception as exc:
            return self._create_failure_page(
                request_form=request_form,
                message="The documentation workflow could not be completed.",
                error_message=str(exc),
            )

        return self._map_workflow_result(
            workflow_result=workflow_result,
            request_form=request_form,
        )

    def submit_review_decision(
        self,
        workflow_id: str,
        proposal_id: str,
        decision: ReviewDecision,
        feedback: str | None = None,
    ) -> DocumentationAgentPageView:
        """Submit one review decision and return updated page state."""

        request_form = DocumentationRequestForm()

        if self.review_service is None:
            return self._create_failure_page(
                request_form=request_form,
                message="Review processing is unavailable.",
                error_message="No documentation review service is configured.",
            )

        try:
            review_result = self.review_service.submit_decision(
                workflow_id=workflow_id,
                proposal_id=proposal_id,
                decision=decision,
                feedback=self._normalize_optional_text(feedback),
            )
        except Exception as exc:
            return self._create_failure_page(
                request_form=request_form,
                message="The review decision could not be processed.",
                error_message=str(exc),
                workflow_id=workflow_id,
            )

        return self._map_workflow_result(
            workflow_result=review_result,
            request_form=request_form,
        )

    def _build_request_form(
        self,
        user_request: str,
        target_paths: Sequence[str] | None,
    ) -> DocumentationRequestForm:
        """Normalize browser form values."""

        normalized_request = user_request.strip()
        normalized_paths = tuple(
            path.strip()
            for path in (target_paths or ())
            if path is not None and path.strip()
        )

        return DocumentationRequestForm(
            user_request=normalized_request,
            target_paths=normalized_paths,
        )

    def _create_workflow_request(
        self,
        request_form: DocumentationRequestForm,
    ) -> object:
        """
        Create the workflow request expected by the existing service.

        The first-pass adapter returns a simple mapping so that the UI layer
        remains independent of route form objects. Replace this mapping with
        the established Documentation Workflow request model when wiring the
        concrete Phase 6 service.
        """

        return {
            "user_request": request_form.user_request,
            "target_paths": request_form.target_paths,
        }

    def _map_workflow_result(
        self,
        workflow_result: object,
        request_form: DocumentationRequestForm,
    ) -> DocumentationAgentPageView:
        """Convert a workflow result into a complete page view."""

        workflow_id = self._read_value(workflow_result, "workflow_id")
        proposals = self._map_proposals(
            self._read_value(workflow_result, "proposals", default=())
        )
        preliminary_validation = self._map_validation_result(
            self._read_value(
                workflow_result,
                "preliminary_validation",
                default=None,
            )
        )
        final_validation = self._map_validation_result(
            self._read_value(
                workflow_result,
                "final_validation",
                default=None,
            )
        )
        summary = self._map_summary(
            self._read_value(workflow_result, "summary", default=None)
        )
        warnings = tuple(
            str(item)
            for item in self._read_value(
                workflow_result,
                "warnings",
                default=(),
            )
        )
        error_message = self._normalize_optional_text(
            self._read_value(
                workflow_result,
                "error_message",
                default=None,
            )
        )

        page_status = self._determine_page_status(
            workflow_result=workflow_result,
            proposals=proposals,
            warnings=warnings,
            error_message=error_message,
        )

        return DocumentationAgentPageView(
            page_status=page_status,
            status_message=self._status_message(page_status),
            request_form=request_form,
            workflow_id=self._normalize_optional_text(workflow_id),
            proposals=proposals,
            preliminary_validation=preliminary_validation,
            final_validation=final_validation,
            workflow_summary=summary,
            warnings=warnings,
            error_message=error_message,
        )

    def _map_proposals(
        self,
        proposals: object,
    ) -> tuple[DocumentationProposalView, ...]:
        """Map workflow proposals into proposal view models."""

        if not proposals:
            return ()

        return tuple(
            DocumentationProposalView(
                proposal_id=str(
                    self._read_value(proposal, "proposal_id", default="")
                ),
                repository_path=str(
                    self._read_value(proposal, "repository_path", default="")
                ),
                rationale=str(
                    self._read_value(proposal, "rationale", default="")
                ),
                original_content=str(
                    self._read_value(proposal, "original_content", default="")
                ),
                proposed_content=str(
                    self._read_value(proposal, "proposed_content", default="")
                ),
                selected_decision=self._map_review_decision(
                    self._read_value(
                        proposal,
                        "selected_decision",
                        default=None,
                    )
                ),
                feedback=self._normalize_optional_text(
                    self._read_value(proposal, "feedback", default=None)
                ),
                difference=self._map_difference(
                    self._read_value(proposal, "difference", default=None)
                ),
            )
            for proposal in proposals
        )

    def _map_validation_result(
        self,
        validation_result: object | None,
    ) -> ValidationResultView | None:
        """Map a validation result into browser presentation state."""

        if validation_result is None:
            return None

        status = self._map_validation_status(
            self._read_value(
                validation_result,
                "status",
                default=ValidationDisplayStatus.NOT_RUN,
            )
        )
        messages = tuple(
            ValidationMessageView(
                validator_name=str(
                    self._read_value(message, "validator_name", default="")
                ),
                message=str(
                    self._read_value(message, "message", default="")
                ),
                severity=str(
                    self._read_value(message, "severity", default="")
                ),
                repository_path=self._normalize_optional_text(
                    self._read_value(
                        message,
                        "repository_path",
                        default=None,
                    )
                ),
                line_number=self._read_value(
                    message,
                    "line_number",
                    default=None,
                ),
            )
            for message in self._read_value(
                validation_result,
                "messages",
                default=(),
            )
        )

        return ValidationResultView(
            status=status,
            title=str(
                self._read_value(
                    validation_result,
                    "title",
                    default=self._validation_title(status),
                )
            ),
            summary=str(
                self._read_value(
                    validation_result,
                    "summary",
                    default="",
                )
            ),
            error_count=int(
                self._read_value(
                    validation_result,
                    "error_count",
                    default=0,
                )
            ),
            warning_count=int(
                self._read_value(
                    validation_result,
                    "warning_count",
                    default=0,
                )
            ),
            messages=messages,
        )

    def _map_difference(
        self,
        difference: object | None,
    ) -> DocumentationDifferenceView | None:
        """Map one documentation difference into display lines."""

        if difference is None:
            return None

        lines = tuple(
            DifferenceLineView(
                line_type=self._map_difference_line_type(
                    self._read_value(
                        line,
                        "line_type",
                        default=DifferenceLineType.CONTEXT,
                    )
                ),
                content=str(
                    self._read_value(line, "content", default="")
                ),
                old_line_number=self._read_value(
                    line,
                    "old_line_number",
                    default=None,
                ),
                new_line_number=self._read_value(
                    line,
                    "new_line_number",
                    default=None,
                ),
            )
            for line in self._read_value(difference, "lines", default=())
        )

        return DocumentationDifferenceView(
            repository_path=str(
                self._read_value(
                    difference,
                    "repository_path",
                    default="",
                )
            ),
            lines=lines,
        )

    def _map_summary(
        self,
        summary: object | None,
    ) -> DocumentationWorkflowSummaryView | None:
        """Map workflow counters into a display summary."""

        if summary is None:
            return None

        return DocumentationWorkflowSummaryView(
            proposed_count=int(
                self._read_value(summary, "proposed_count", default=0)
            ),
            approved_count=int(
                self._read_value(summary, "approved_count", default=0)
            ),
            revised_count=int(
                self._read_value(summary, "revised_count", default=0)
            ),
            rejected_count=int(
                self._read_value(summary, "rejected_count", default=0)
            ),
            skipped_count=int(
                self._read_value(summary, "skipped_count", default=0)
            ),
            applied_count=int(
                self._read_value(summary, "applied_count", default=0)
            ),
            failed_count=int(
                self._read_value(summary, "failed_count", default=0)
            ),
        )

    def _determine_page_status(
        self,
        workflow_result: object,
        proposals: tuple[DocumentationProposalView, ...],
        warnings: tuple[str, ...],
        error_message: str | None,
    ) -> DocumentationAgentPageStatus:
        """Determine the page status from a workflow result."""

        explicit_status = self._read_value(
            workflow_result,
            "page_status",
            default=None,
        )
        if explicit_status is not None:
            try:
                return DocumentationAgentPageStatus(str(explicit_status))
            except ValueError:
                pass

        if error_message:
            return DocumentationAgentPageStatus.FAILED

        if proposals and any(not proposal.has_decision for proposal in proposals):
            return DocumentationAgentPageStatus.REVIEW_REQUIRED

        completed = bool(
            self._read_value(workflow_result, "completed", default=False)
        )
        if completed and warnings:
            return DocumentationAgentPageStatus.COMPLETED_WITH_WARNINGS
        if completed:
            return DocumentationAgentPageStatus.COMPLETED

        return DocumentationAgentPageStatus.PROCESSING

    @staticmethod
    def _map_review_decision(value: object | None) -> ReviewDecision | None:
        """Convert an optional decision value to ReviewDecision."""

        if value is None or isinstance(value, ReviewDecision):
            return value

        try:
            return ReviewDecision(str(value))
        except ValueError:
            return None

    @staticmethod
    def _map_validation_status(value: object) -> ValidationDisplayStatus:
        """Convert a validation status value to the display enum."""

        if isinstance(value, ValidationDisplayStatus):
            return value

        try:
            return ValidationDisplayStatus(str(value))
        except ValueError:
            return ValidationDisplayStatus.NOT_RUN

    @staticmethod
    def _map_difference_line_type(value: object) -> DifferenceLineType:
        """Convert a difference line value to the display enum."""

        if isinstance(value, DifferenceLineType):
            return value

        try:
            return DifferenceLineType(str(value))
        except ValueError:
            return DifferenceLineType.CONTEXT

    @staticmethod
    def _validation_title(status: ValidationDisplayStatus) -> str:
        """Return a default title for a validation state."""

        titles = {
            ValidationDisplayStatus.NOT_RUN: "Validation not run",
            ValidationDisplayStatus.PASSED: "Validation passed",
            ValidationDisplayStatus.PASSED_WITH_WARNINGS: (
                "Validation passed with warnings"
            ),
            ValidationDisplayStatus.FAILED: "Validation failed",
        }
        return titles[status]

    @staticmethod
    def _status_message(
        status: DocumentationAgentPageStatus,
    ) -> str:
        """Return the default display message for a page status."""

        messages = {
            DocumentationAgentPageStatus.READY: (
                "Ready for a documentation request."
            ),
            DocumentationAgentPageStatus.PROCESSING: (
                "The documentation workflow is processing."
            ),
            DocumentationAgentPageStatus.REVIEW_REQUIRED: (
                "Review the proposed documentation changes."
            ),
            DocumentationAgentPageStatus.COMPLETED: (
                "The documentation workflow completed successfully."
            ),
            DocumentationAgentPageStatus.COMPLETED_WITH_WARNINGS: (
                "The documentation workflow completed with warnings."
            ),
            DocumentationAgentPageStatus.FAILED: (
                "The documentation workflow failed."
            ),
        }
        return messages[status]

    def _create_failure_page(
        self,
        request_form: DocumentationRequestForm,
        message: str,
        error_message: str,
        workflow_id: str | None = None,
    ) -> DocumentationAgentPageView:
        """Create a consistent failure page."""

        return DocumentationAgentPageView(
            page_status=DocumentationAgentPageStatus.FAILED,
            status_message=message,
            request_form=request_form,
            workflow_id=workflow_id,
            error_message=error_message,
        )

    @staticmethod
    def _normalize_optional_text(value: object | None) -> str | None:
        """Normalize an optional value to stripped text."""

        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _read_value(
        source: object,
        name: str,
        default: object = None,
    ) -> object:
        """Read a value from either an object attribute or a mapping."""

        if isinstance(source, dict):
            return source.get(name, default)

        return getattr(source, name, default)
