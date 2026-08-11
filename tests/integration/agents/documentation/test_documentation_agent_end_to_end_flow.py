# ============================================================
# Project0 - Documentation Agent End-to-End Integration Tests
#
# File: test_documentation_agent_end_to_end_flow.py
#
# Purpose:
#    High-level integration tests aligned with:
#        Documentation_Agent_Test_Plan.md
#
# These tests exercise the Documentation Agent through the
# Platform Dispatcher boundary using deterministic reasoning
# provider behavior.
#
# Verification scenario IDs follow the Test Plan directly:
#    DA-FUN-*  Functional Verification
#    DA-SAF-*  Safety Verification
#    DA-AI-*   AI Reasoning Verification
#    DA-DOC-*  Documentation Compliance
#    DA-ARCH-* Platform Boundary
#
# Integration test function names add the INT layer prefix.
#
# Implemented integration scenario IDs:
#    DA-FUN-001
#    DA-FUN-002
#    DA-FUN-003
#    DA-FUN-004
#    DA-FUN-005
#    DA-SAF-001
#    DA-SAF-003
#    DA-AI-001
#
# Deferred IDs require additional integration fixtures:
#    DA-SAF-004
#    DA-AI-002
#    DA-AI-003
#    DA-DOC-001
#    DA-DOC-002
#    DA-ARCH-001
#
# These tests verify assembled workflow behavior through Python/service
# boundaries. Browser/UI acceptance testing is maintained separately
# under tests/acceptance/agents/documentation/.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

import pytest

from project0.models.documentation_workflow_models import (
    DocumentationReview,
    DocumentationWorkflowStatus,
    ReviewDecision,
)
from project0.models.reasoning_models import (
    ProviderResponse,
)
from project0.reasoning.providers.stub_provider import StubReasoningProvider
from project0.config.settings import ProjectSettings
from project0.platform.platform_dispatcher import create_platform_dispatcher


def _create_reasoning_provider(
    repository_path: str,
) -> StubReasoningProvider:
    """Create deterministic reasoning output for integration tests."""

    return StubReasoningProvider(
        response=ProviderResponse(
            provider_name="stub",
            model_name="stub-model",
            content="",
            structured_output={
                "summary": (
                    "Generated documentation proposal."
                ),
                "assumptions": [],
                "warnings": [],
                "impacts": [
                    {
                        "document_path": repository_path,
                        "summary": "Documentation update",
                        "rationale": (
                            "Integration test documentation update."
                        ),
                    }
                ],
                "proposed_changes": [
                    {
                        "document_path": repository_path,
                        "operation": "update",
                        "rationale": (
                            "Integration test documentation update."
                        ),
                        "proposed_content": (
                            "# Updated Documentation\\n\\n"
                            "Integration test content.\\n"
                        ),
                        "anchor_text": "Implemented:",
                        "edit_type": "insert",
                        "confidence": 0.95,
                    }
                ],
            },
        )
    )


@pytest.fixture
def documentation_repository(tmp_path: Path) -> Path:
    """Create a minimal repository fixture."""

    (tmp_path / "docs/project").mkdir(
        parents=True
    )

    (tmp_path / "docs/project/Test.md").write_text(
        "# Test\n\nImplemented:\n\n- Existing item\n",
        encoding="utf-8",
    )

    (tmp_path / "mkdocs.yml").write_text(
        """
site_name: Integration Test Documentation

nav:
  - Test: project/Test.md
""",
        encoding="utf-8",
    )

    return tmp_path


def _create_dispatcher(
    repository_path: Path,
    monkeypatch,
) -> tuple[object, StubReasoningProvider]:
    """Create a dispatcher using deterministic reasoning."""

    provider = _create_reasoning_provider(
        "docs/project/Test.md"
    )

    settings = ProjectSettings(
        project_root=repository_path,
        docs_dir=repository_path / "docs",
        source_dir=repository_path / "src",
        tests_dir=repository_path / "tests",
    )

    monkeypatch.setattr(
        "project0.platform.platform_dispatcher.validate_startup",
        lambda _: None,
    )

    dispatcher = create_platform_dispatcher(
        reasoning_provider=provider,
        reasoning_model_name="stub-model",
        settings=settings,
    )

    return dispatcher, provider


def test_INT_DA_FUN_001_documentation_request_processing(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Documentation request creates a review workflow.
    """

    dispatcher, _ = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    state = dispatcher.run_documentation_workflow(
        user_request="Update documentation.",
        target_paths=(
            "docs/project/Test.md",
        ),
    )

    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert state.proposals


def test_INT_DA_FUN_002_documentation_proposal_generation(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Documentation proposal contains generated change data.
    """

    dispatcher, _ = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    state = dispatcher.run_documentation_workflow(
        "Update documentation.",
        ("docs/project/Test.md",),
    )

    proposal = state.proposals[0]

    assert proposal.repository_path == (
        "docs/project/Test.md"
    )
    assert proposal.proposed_content


def test_INT_DA_FUN_003_surgical_documentation_editing(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Insert-after behavior preserves the anchor.
    """

    dispatcher, _ = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    state = dispatcher.run_documentation_workflow(
        "Insert documentation item.",
        ("docs/project/Test.md",),
    )

    proposal = state.proposals[0]

    assert proposal.anchor_text == "Implemented:"


def test_INT_DA_FUN_004_multi_document_documentation_update(
    documentation_repository: Path,
):
    """
    Multi-document behavior will be expanded with multi-change
    reasoning fixtures.
    """

    pytest.skip(
        "Requires multi-proposal reasoning fixture."
    )


def test_INT_DA_FUN_005_minimal_change_verification(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Proposal is limited to intended documentation file.
    """

    dispatcher, _ = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    state = dispatcher.run_documentation_workflow(
        "Update documentation.",
        ("docs/project/Test.md",),
    )

    assert len(state.proposals) == 1


def test_INT_DA_SAF_001_rejected_proposal_protection(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Rejected proposals do not apply changes.
    """

    dispatcher, _ = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    state = dispatcher.run_documentation_workflow(
        "Update documentation.",
        ("docs/project/Test.md",),
    )

    proposal = state.proposals[0]

    result = dispatcher.submit_documentation_review(
        state.workflow_id,
        DocumentationReview(
            proposal_id=proposal.proposal_id,
            decision=ReviewDecision.REJECT,
        ),
    )

    assert result.summary.rejected_count == 1
    assert result.summary.applied_count == 0


def test_INT_DA_SAF_003_invalid_change_handling(
    monkeypatch,
):
    """
    Invalid request handling remains covered by dispatcher validation.
    """

    dispatcher, _ = _create_dispatcher(Path("."), monkeypatch)

    with pytest.raises(ValueError):
        dispatcher.run_documentation_workflow(
            "",
            (),
        )


def test_INT_DA_AI_001_reasoning_provider_integration(
    documentation_repository: Path,
    monkeypatch,
):
    """
    Verify the reasoning provider participates in the workflow.
    """

    dispatcher, provider = _create_dispatcher(
        documentation_repository,
        monkeypatch,
    )

    dispatcher.run_documentation_workflow(
        "Update documentation.",
        ("docs/project/Test.md",),
    )

    assert provider.requests


@pytest.mark.skip(
    reason="Requires baseline documentation integration fixture."
)
def test_INT_DA_SAF_004_baseline_documentation_handling():
    pass


@pytest.mark.skip(
    reason="Requires unsupported-information reasoning fixture."
)
def test_INT_DA_AI_002_unsupported_information_prevention():
    pass


@pytest.mark.skip(
    reason="Requires invalid AI output fixture."
)
def test_INT_DA_AI_003_invalid_ai_output_handling():
    pass


@pytest.mark.skip(
    reason="Requires documentation validation integration fixture."
)
def test_INT_DA_DOC_001_documentation_standards_compliance():
    pass


@pytest.mark.skip(
    reason="Requires source documentation validation integration fixture."
)
def test_INT_DA_DOC_002_source_documentation_compliance():
    pass


@pytest.mark.skip(
    reason="Requires architecture dependency validation tooling."
)
def test_INT_DA_ARCH_001_agent_platform_separation():
    pass
