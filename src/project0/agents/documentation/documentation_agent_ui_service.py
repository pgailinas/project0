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
from datetime import UTC, datetime
from difflib import ndiff
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
from project0.models.documentation_workflow_models import (
    DocumentationReview,
    DocumentationWorkflowStatus,
    ReviewDecision,
)
from project0.repository.repository_update_service import (
    apply_documentation_change,
)


DIFFERENCE_CONTEXT_LINES = 3


class DocumentationWorkflowPort(Protocol):
    """Minimal documentation workflow interface required by the UI."""

    def run_documentation_workflow(
        self,
        user_request: str,
        target_paths: tuple[str, ...] = (),
        workflow_id: str | None = None,
    ) -> object:
        """Execute a documentation workflow until review or completion."""

    def submit_documentation_review(
        self,
        workflow_id: str,
        review: DocumentationReview,
    ) -> object:
        """Submit one user review and continue the workflow."""


@dataclass(frozen=True, slots=True)
class DocumentationAgentUIService:
    """Coordinate Documentation Agent UI requests and presentation state."""

    workflow: DocumentationWorkflowPort

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
            workflow_result = self.workflow.run_documentation_workflow(
                user_request=request_form.user_request,
                target_paths=request_form.target_paths,
            )
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

        try:
            review_result = self.workflow.submit_documentation_review(
                workflow_id=workflow_id,
                review=DocumentationReview(
                    proposal_id=proposal_id,
                    decision=decision,
                    feedback=self._normalize_optional_text(feedback),
                    reviewed_at=datetime.now(UTC),
                ),
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

    def _map_workflow_result(
        self,
        workflow_result: object,
        request_form: DocumentationRequestForm,
    ) -> DocumentationAgentPageView:
        """Convert a workflow result into a complete page view."""

        workflow_id = self._read_value(workflow_result, "workflow_id")
        proposals = self._map_proposals(
            self._read_value(workflow_result, "proposals", default=()),
            self._read_value(workflow_result, "reviews", default=()),
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
        reviews: object = (),
    ) -> tuple[DocumentationProposalView, ...]:
        """Map workflow proposals and reviews into proposal view models."""

        if not proposals:
            return ()

        reviews_by_proposal = {
            str(self._read_value(review, "proposal_id", default="")): review
            for review in (reviews or ())
        }

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
                        reviews_by_proposal.get(
                            str(self._read_value(
                                proposal,
                                "proposal_id",
                                default="",
                            )),
                            {},
                        ),
                        "decision",
                        default=None,
                    )
                ),
                feedback=self._normalize_optional_text(
                    self._read_value(
                        reviews_by_proposal.get(
                            str(self._read_value(
                                proposal,
                                "proposal_id",
                                default="",
                            )),
                            {},
                        ),
                        "feedback",
                        default=None,
                    )
                ),
                difference=self._create_proposal_difference(proposal),
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
        issues = tuple(
            self._read_value(
                validation_result,
                "issues",
                default=(),
            )
        )
        messages = tuple(
            ValidationMessageView(
                validator_name=str(
                    self._read_value(issue, "validator_name", default="")
                ),
                message=str(
                    self._read_value(issue, "message", default="")
                ),
                severity=str(
                    self._read_value(issue, "severity", default="")
                ),
                repository_path=self._normalize_optional_text(
                    self._read_value(
                        issue,
                        "repository_path",
                        default=None,
                    )
                ),
                line_number=self._read_value(
                    issue,
                    "line_number",
                    default=None,
                ),
            )
            for issue in issues
        )
        error_count = sum(
            str(
                self._read_value(
                    issue,
                    "severity",
                    default="",
                )
            ) == "error"
            for issue in issues
        )
        warning_count = sum(
            str(
                self._read_value(
                    issue,
                    "severity",
                    default="",
                )
            ) == "warning"
            for issue in issues
        )
        summary = self._normalize_optional_text(
            self._read_value(
                validation_result,
                "error_message",
                default=None,
            )
        ) or (
            f"{error_count} error(s), "
            f"{warning_count} warning(s)."
        )

        return ValidationResultView(
            status=status,
            title=self._validation_title(status),
            summary=summary,
            error_count=error_count,
            warning_count=warning_count,
            messages=messages,
        )

    def _create_proposal_difference(
        self,
        proposal: object,
    ) -> DocumentationDifferenceView:
        """Create a display difference from proposal content."""

        repository_path = str(
            self._read_value(proposal, "repository_path", default="")
        )
        original_content = str(
            self._read_value(proposal, "original_content", default="")
        )
        proposed_content = str(
            self._read_value(proposal, "proposed_content", default="")
        )
        anchor_text = self._normalize_optional_text(
            self._read_value(
                proposal,
                "anchor_text",
                default=None,
            )
        )

        candidate_content = apply_documentation_change(
            original_content=original_content,
            proposed_content=proposed_content,
            anchor_text=anchor_text,
        )

        original_lines = original_content.splitlines()
        proposed_lines = candidate_content.splitlines()

        old_line_number = 0
        new_line_number = 0
        lines: list[DifferenceLineView] = []

        for line in ndiff(original_lines, proposed_lines):
            prefix = line[:2]
            content = line[2:]

            if prefix == "  ":
                old_line_number += 1
                new_line_number += 1
                lines.append(DifferenceLineView(
                    line_type=DifferenceLineType.CONTEXT,
                    content=content,
                    old_line_number=old_line_number,
                    new_line_number=new_line_number,
                ))
            elif prefix == "- ":
                old_line_number += 1
                lines.append(DifferenceLineView(
                    line_type=DifferenceLineType.REMOVED,
                    content=content,
                    old_line_number=old_line_number,
                ))
            elif prefix == "+ ":
                new_line_number += 1
                lines.append(DifferenceLineView(
                    line_type=DifferenceLineType.ADDED,
                    content=content,
                    new_line_number=new_line_number,
                ))

        return DocumentationDifferenceView(
            repository_path=repository_path,
            lines=self._focus_difference_lines(lines),
        )

    @staticmethod
    def _focus_difference_lines(
        lines: Sequence[DifferenceLineView],
    ) -> tuple[DifferenceLineView, ...]:
        """Keep changed lines with limited surrounding review context."""

        changed_indexes = {
            index
            for index, line in enumerate(lines)
            if line.line_type is not DifferenceLineType.CONTEXT
        }
        if not changed_indexes:
            return tuple(lines)

        visible_indexes: set[int] = set()
        for index in changed_indexes:
            start = max(0, index - DIFFERENCE_CONTEXT_LINES)
            stop = min(
                len(lines),
                index + DIFFERENCE_CONTEXT_LINES + 1,
            )
            visible_indexes.update(range(start, stop))

        return tuple(
            line
            for index, line in enumerate(lines)
            if index in visible_indexes
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

        workflow_status = self._map_workflow_status(
            self._read_value(workflow_result, "status", default=None)
        )

        if workflow_status is DocumentationWorkflowStatus.REVIEW_REQUIRED:
            return DocumentationAgentPageStatus.REVIEW_REQUIRED
        if workflow_status is DocumentationWorkflowStatus.FAILED:
            return DocumentationAgentPageStatus.FAILED
        if (
            workflow_status
            is DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
        ):
            return DocumentationAgentPageStatus.COMPLETED_WITH_WARNINGS
        if workflow_status is DocumentationWorkflowStatus.COMPLETED:
            return DocumentationAgentPageStatus.COMPLETED

        if proposals and any(
            not proposal.has_decision
            for proposal in proposals
        ):
            return DocumentationAgentPageStatus.REVIEW_REQUIRED

        return DocumentationAgentPageStatus.PROCESSING

    @staticmethod
    def _map_workflow_status(
        value: object | None,
    ) -> DocumentationWorkflowStatus | None:
        """Convert an optional workflow status value."""

        if value is None or isinstance(value, DocumentationWorkflowStatus):
            return value

        try:
            return DocumentationWorkflowStatus(str(value))
        except ValueError:
            return None

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
