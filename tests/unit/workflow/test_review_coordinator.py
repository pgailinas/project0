# ============================================================
# Project0 - Review Coordinator Tests
#
# File: test_review_coordinator.py
#
# Purpose:
#     Verify individual documentation proposal review decisions
#     coordinated by the Project0 Review Coordinator.
#
# ============================================================

from datetime import UTC

import pytest

from project0.models.documentation_workflow_models import (
    DocumentationChangeProposal,
    ReviewDecision,
)
from project0.workflow.review_coordinator import ReviewCoordinator


def _proposal() -> DocumentationChangeProposal:
    """Create a standard documentation change proposal."""

    return DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the document heading.",
        proposal_id="proposal-001",
    )


def test_approve_decision_returns_review() -> None:
    """An approve decision returns a completed review."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.APPROVE,
            None,
        )
    )

    review = coordinator.review(_proposal())

    assert review.proposal_id == "proposal-001"
    assert review.decision is ReviewDecision.APPROVE
    assert review.feedback is None
    assert review.reviewed_at is not None
    assert review.reviewed_at.tzinfo is UTC


def test_revise_decision_preserves_feedback() -> None:
    """A revise decision preserves normalized feedback."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.REVISE,
            "  Clarify the architecture description.  ",
        )
    )

    review = coordinator.review(_proposal())

    assert review.decision is ReviewDecision.REVISE
    assert review.feedback == "Clarify the architecture description."


def test_reject_decision_preserves_optional_feedback() -> None:
    """A reject decision may include feedback."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.REJECT,
            "The proposed change is unnecessary.",
        )
    )

    review = coordinator.review(_proposal())

    assert review.decision is ReviewDecision.REJECT
    assert review.feedback == "The proposed change is unnecessary."


def test_skip_decision_returns_review() -> None:
    """A skip decision returns a completed review."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.SKIP,
            None,
        )
    )

    review = coordinator.review(_proposal())

    assert review.decision is ReviewDecision.SKIP
    assert review.feedback is None


def test_blank_feedback_is_normalized_to_none() -> None:
    """Blank optional feedback is normalized to None."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.APPROVE,
            "   ",
        )
    )

    review = coordinator.review(_proposal())

    assert review.feedback is None


def test_revise_without_feedback_raises_value_error() -> None:
    """A revise decision requires meaningful feedback."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.REVISE,
            None,
        )
    )

    with pytest.raises(
        ValueError,
        match="A revise decision requires review feedback.",
    ):
        coordinator.review(_proposal())


def test_revise_with_blank_feedback_raises_value_error() -> None:
    """Blank feedback does not satisfy a revise decision."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.REVISE,
            "   ",
        )
    )

    with pytest.raises(
        ValueError,
        match="A revise decision requires review feedback.",
    ):
        coordinator.review(_proposal())


def test_invalid_decision_type_raises_type_error() -> None:
    """A decision provider must return a ReviewDecision."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            "approve",
            None,
        )
    )

    with pytest.raises(
        TypeError,
        match=(
            "The review decision provider must return a ReviewDecision."
        ),
    ):
        coordinator.review(_proposal())


def test_proposal_is_forwarded_to_decision_provider() -> None:
    """The original proposal is passed to the decision provider."""

    received_proposals: list[DocumentationChangeProposal] = []

    def decision_provider(
        proposal: DocumentationChangeProposal,
    ) -> tuple[ReviewDecision, str | None]:
        received_proposals.append(proposal)

        return ReviewDecision.APPROVE, None

    proposal = _proposal()
    coordinator = ReviewCoordinator(
        decision_provider=decision_provider,
    )

    coordinator.review(proposal)

    assert received_proposals == [proposal]


def test_each_review_receives_current_timestamp() -> None:
    """Each review receives a timezone-aware current timestamp."""

    coordinator = ReviewCoordinator(
        decision_provider=lambda proposal: (
            ReviewDecision.APPROVE,
            None,
        )
    )

    first_review = coordinator.review(_proposal())
    second_review = coordinator.review(_proposal())

    assert first_review.reviewed_at is not None
    assert second_review.reviewed_at is not None
    assert first_review.reviewed_at.tzinfo is UTC
    assert second_review.reviewed_at.tzinfo is UTC
    assert second_review.reviewed_at >= first_review.reviewed_at
