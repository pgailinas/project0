# ============================================================
# Project0 - Research Evaluation Service Tests
#
# File: test_research_evaluation_service.py
#
# Purpose:
#     Verify research evaluation orchestration, structured
#     output parsing, score handling, and failure behavior.
#
# ============================================================

from __future__ import annotations

from project0.agents.research.research_evaluation_service import (
    ResearchEvaluationService,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchRequest,
    ResearchSourceReference,
    ResearchStrategy,
)


class StubProvider:
    """Provide deterministic provider behavior for testing."""

    def __init__(
        self,
        response: ProviderResponse,
        error: Exception | None = None,
    ) -> None:
        """Initialize the configured provider response or error."""

        self.response = response
        self.error = error
        self.requests: list[ProviderRequest] = []

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Return the configured provider response or error."""

        self.requests.append(request)

        if self.error is not None:
            raise self.error

        return self.response


def create_research_request() -> ResearchRequest:
    """Create a research request for testing."""

    return ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        constraints=(
            "Focus on vision-language alignment.",
        ),
        focus_areas=(
            "video representation learning",
        ),
    )


def create_research_strategy() -> ResearchStrategy:
    """Create a research strategy for testing."""

    return ResearchStrategy(
        concepts=(
            "self-supervised learning",
            "video representation learning",
        ),
        search_terms=(
            "self-supervised video representation VideoQA",
        ),
    )


def create_source_reference(
    source_id: str = "paper-001",
    title: str = "Example Video Representation Paper",
) -> ResearchSourceReference:
    """Create a research source reference for testing."""

    return ResearchSourceReference(
        source_name="semantic_scholar",
        source_id=source_id,
        title=title,
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
    )


def create_paper_metadata(
    source_id: str = "paper-001",
    title: str = "Example Video Representation Paper",
) -> PaperMetadata:
    """Create paper metadata for testing."""

    reference = create_source_reference(
        source_id=source_id,
        title=title,
    )

    return PaperMetadata(
        source_reference=reference,
        title=title,
        authors=reference.authors,
        publication_year=2024,
        abstract="Example abstract.",
        venue="Example Conference",
    )


def create_valid_provider_response(
    evaluations: list[dict] | None = None,
) -> ProviderResponse:
    """Create a valid structured provider response."""

    return ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output={
            "evaluations": (
                evaluations
                if evaluations is not None
                else [
                    {
                        "source_id": "paper-001",
                        "relevance_score": 0.95,
                        "relevance_summary": (
                            "The paper is highly relevant to "
                            "the research question."
                        ),
                        "strengths": [
                            "Uses semantic representation learning.",
                        ],
                        "limitations": [
                            "Limited VideoQA evaluation.",
                        ],
                        "research_connections": [
                            (
                                "Supports a vision-language "
                                "alignment experiment."
                            ),
                        ],
                        "warnings": [],
                    }
                ]
            ),
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )


def test_research_evaluation_service_creates_evaluation() -> None:
    """Verify successful research evaluation creation."""

    paper = create_paper_metadata()
    provider = StubProvider(
        create_valid_provider_response()
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert len(result) == 1

    evaluation = result[0]

    assert evaluation.paper == paper
    assert evaluation.relevance_score == 0.95
    assert evaluation.relevance_summary == (
        "The paper is highly relevant to "
        "the research question."
    )
    assert evaluation.strengths == (
        "Uses semantic representation learning.",
    )
    assert evaluation.limitations == (
        "Limited VideoQA evaluation.",
    )
    assert evaluation.research_connections == (
        "Supports a vision-language alignment experiment.",
    )
    assert evaluation.warnings == ()


def test_research_evaluation_service_invokes_provider() -> None:
    """Verify provider orchestration."""

    provider = StubProvider(
        create_valid_provider_response()
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(provider.requests) == 1

    provider_request = provider.requests[0]

    assert provider_request.model_name == "qwen3:8b"
    assert provider_request.temperature == 0.0
    assert provider_request.metadata[
        "paper_count"
    ] == 1


def test_research_evaluation_service_returns_empty_for_no_papers() -> None:
    """Verify empty paper input avoids provider execution."""

    provider = StubProvider(
        create_valid_provider_response()
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (),
    )

    assert result == ()
    assert provider.requests == []


def test_research_evaluation_service_supports_multiple_papers() -> None:
    """Verify multiple paper evaluations are parsed."""

    first_paper = create_paper_metadata(
        source_id="paper-001",
        title="First Paper",
    )
    second_paper = create_paper_metadata(
        source_id="paper-002",
        title="Second Paper",
    )

    provider_response = create_valid_provider_response(
        evaluations=[
            {
                "source_id": "paper-001",
                "relevance_score": 0.9,
                "relevance_summary": "First paper is relevant.",
                "strengths": [],
                "limitations": [],
                "research_connections": [],
                "warnings": [],
            },
            {
                "source_id": "paper-002",
                "relevance_score": 0.7,
                "relevance_summary": "Second paper is relevant.",
                "strengths": [],
                "limitations": [],
                "research_connections": [],
                "warnings": [],
            },
        ]
    )

    service = ResearchEvaluationService(
        provider=StubProvider(provider_response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (
            first_paper,
            second_paper,
        ),
    )

    assert len(result) == 2
    assert result[0].paper == first_paper
    assert result[1].paper == second_paper


def test_research_evaluation_service_allows_null_score() -> None:
    """Verify nullable relevance score parsing."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = None

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score is None


def test_research_evaluation_service_normalizes_percentage_score() -> None:
    """Verify percentage relevance scores are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 95

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.95


def test_research_evaluation_service_normalizes_percentage_string() -> None:
    """Verify percentage string scores are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = "95%"

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.95


def test_research_evaluation_service_normalizes_decimal_string() -> None:
    """Verify decimal string scores are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = "0.95"

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.95


def test_research_evaluation_service_rejects_missing_structured_output() -> None:
    """Verify missing structured output is rejected."""

    response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="Unstructured output.",
    )

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except ValueError as error:
        assert str(error) == (
            "Provider response did not include structured output."
        )
    else:
        raise AssertionError("Expected missing structured output failure.")


def test_research_evaluation_service_rejects_invalid_evaluations_type() -> None:
    """Verify evaluations must be a list."""

    response = create_valid_provider_response()
    response.structured_output["evaluations"] = {}

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == "evaluations must be a list."
    else:
        raise AssertionError("Expected invalid evaluations failure.")


def test_research_evaluation_service_rejects_invalid_item() -> None:
    """Verify each evaluation must be an object."""

    response = create_valid_provider_response(
        evaluations=["invalid evaluation"]
    )

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == "evaluation must be an object."
    else:
        raise AssertionError("Expected invalid evaluation item failure.")


def test_research_evaluation_service_rejects_unknown_source_id() -> None:
    """Verify unknown evaluation source identifiers are rejected."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-999"

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except ValueError as error:
        assert "unknown source identifier" in str(error)
    else:
        raise AssertionError("Expected unknown source identifier failure.")


def test_research_evaluation_service_rejects_duplicate_source_id() -> None:
    """Verify duplicate evaluation source identifiers are rejected."""

    duplicate = create_valid_provider_response().structured_output[
        "evaluations"
    ][0]

    response = create_valid_provider_response(
        evaluations=[
            duplicate,
            duplicate.copy(),
        ]
    )

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except ValueError as error:
        assert "Duplicate research evaluation source identifier" in str(
            error
        )
    else:
        raise AssertionError("Expected duplicate source identifier failure.")


def test_research_evaluation_service_rejects_missing_paper_evaluation() -> None:
    """Verify every supplied paper requires an evaluation."""

    first_paper = create_paper_metadata(
        source_id="paper-001",
        title="First Paper",
    )
    second_paper = create_paper_metadata(
        source_id="paper-002",
        title="Second Paper",
    )

    service = ResearchEvaluationService(
        provider=StubProvider(
            create_valid_provider_response()
        ),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (
                first_paper,
                second_paper,
            ),
        )
    except ValueError as error:
        assert "did not include evaluations" in str(error)
        assert "paper-002" in str(error)
    else:
        raise AssertionError("Expected missing evaluation failure.")


def test_research_evaluation_service_rejects_invalid_score() -> None:
    """Verify relevance score must be numeric or null."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = "high"

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == (
            "Relevance score must be numeric or null."
        )
    else:
        raise AssertionError("Expected invalid relevance score failure.")


def test_research_evaluation_service_rejects_out_of_range_score() -> None:
    """Verify relevance score must be within supported range."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 1.5

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except ValueError as error:
        assert str(error) == (
            "Relevance score must be between 0.0 and 1.0."
        )
    else:
        raise AssertionError("Expected out-of-range relevance failure.")


def test_research_evaluation_service_rejects_non_string_strengths() -> None:
    """Verify strengths must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["strengths"] = [
        "Valid strength.",
        123,
    ]

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == (
            "strengths must contain strings only."
        )
    else:
        raise AssertionError("Expected invalid strengths failure.")


def test_research_evaluation_service_rejects_non_string_limitations() -> None:
    """Verify limitations must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["limitations"] = [
        123,
    ]

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == (
            "limitations must contain strings only."
        )
    else:
        raise AssertionError("Expected invalid limitations failure.")


def test_research_evaluation_service_rejects_non_string_connections() -> None:
    """Verify research connections must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["research_connections"] = [
        123,
    ]

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == (
            "research_connections must contain strings only."
        )
    else:
        raise AssertionError("Expected invalid connections failure.")


def test_research_evaluation_service_rejects_non_string_warnings() -> None:
    """Verify warnings must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["warnings"] = [
        123,
    ]

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except TypeError as error:
        assert str(error) == (
            "warnings must contain strings only."
        )
    else:
        raise AssertionError("Expected invalid warnings failure.")


def test_research_evaluation_service_propagates_provider_error() -> None:
    """Verify provider failures propagate to workflow handling."""

    service = ResearchEvaluationService(
        provider=StubProvider(
            create_valid_provider_response(),
            error=RuntimeError("Local model server unavailable."),
        ),
        model_name="qwen3:8b",
    )

    try:
        service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (create_paper_metadata(),),
        )
    except RuntimeError as error:
        assert str(error) == "Local model server unavailable."
    else:
        raise AssertionError("Expected provider failure.")


def test_research_evaluation_service_preserves_paper_mapping() -> None:
    """Verify evaluations retain their original paper objects."""

    paper = create_paper_metadata()

    service = ResearchEvaluationService(
        provider=StubProvider(
            create_valid_provider_response()
        ),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].paper is paper
