# ============================================================
# Project0 - Review Coordinator
#
# File: review_coordinator.py
#
# Purpose:
#     Coordinate individual user review decisions for proposed
#     documentation changes.
#
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from project0.models.documentation_workflow_models import (
    DocumentationChangeProposal,
    DocumentationReview,
    ReviewDecision,
)


ReviewDecisionProvider = Callable[
    [DocumentationChangeProposal],
    tuple[ReviewDecision, str | None],
]


class ReviewCoordinator:
    """Coordinate one review decision for each proposed change."""

    def __init__(
        self,
        decision_provider: ReviewDecisionProvider,
    ) -> None:
        self._decision_provider = decision_provider

    def review(
        self,
        proposal: DocumentationChangeProposal,
    ) -> DocumentationReview:
        """Review one documentation change proposal."""

        decision, feedback = self._decision_provider(proposal)

        if not isinstance(decision, ReviewDecision):
            raise TypeError(
                "The review decision provider must return a ReviewDecision."
            )

        normalized_feedback = self._normalize_feedback(feedback)

        if (
            decision is ReviewDecision.REVISE
            and normalized_feedback is None
        ):
            raise ValueError(
                "A revise decision requires review feedback."
            )

        return DocumentationReview(
            proposal_id=proposal.proposal_id,
            decision=decision,
            feedback=normalized_feedback,
            reviewed_at=datetime.now(UTC),
        )

    @staticmethod
    def _normalize_feedback(
        feedback: str | None,
    ) -> str | None:
        """Normalize optional review feedback."""

        if feedback is None:
            return None

        normalized_feedback = feedback.strip()

        if not normalized_feedback:
            return None

        return normalized_feedback
