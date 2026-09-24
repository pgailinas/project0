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

import logging

import pytest

from project0.agents.research.research_evaluation_service import (
    ResearchEvaluationService,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchGuidanceRelevance,
    ResearchMechanismMatch,
    ResearchPaperEvidenceStatus,
    ResearchRequest,
    ResearchSourceReference,
    ResearchStrategy,
)


def add_structured_mechanism_fields(
    evaluation: object,
) -> object:
    """Add internally consistent mechanism evidence to a test response."""

    if not isinstance(evaluation, dict):
        return evaluation

    score = evaluation.get("relevance_score")
    if score is None or not isinstance(score, (int, float)):
        mechanism_match = "none"
    elif score >= 75:
        mechanism_match = "direct"
    elif score >= 50:
        mechanism_match = "transferable"
    elif score >= 25:
        mechanism_match = "adjacent"
    else:
        mechanism_match = "none"

    evaluation.setdefault("mechanism_match", mechanism_match)
    evaluation.setdefault(
        "source_mechanism",
        "Learns semantically aligned visual representations.",
    )
    evaluation.setdefault(
        "target_problem_dimension",
        "Semantic alignment of learned VideoQA representations.",
    )
    evaluation.setdefault(
        "required_adaptation",
        "Apply the representation objective to the target video encoder.",
    )
    evaluation.setdefault(
        "evidence_support",
        ["The supplied abstract describes representation learning."],
    )
    return evaluation


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


class SequentialStubProvider:
    """Provide deterministic sequential responses for retry testing."""

    def __init__(
        self,
        responses: tuple[ProviderResponse, ...],
    ) -> None:
        """Initialize the configured provider responses."""

        self.responses = responses
        self.requests: list[ProviderRequest] = []

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Return the next configured provider response."""

        self.requests.append(request)

        return self.responses[len(self.requests) - 1]


def create_research_request() -> ResearchRequest:
    """Create a research request for testing."""

    return ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        guidance=(
            "Focus on vision-language alignment. "
            "video representation learning"
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
            "evaluations": [
                add_structured_mechanism_fields(evaluation)
                for evaluation in (
                    evaluations
                    if evaluations is not None
                    else [
                    {
                        "source_id": "paper-001",
                        "relevance_score": 95,
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
                                "The paper's semantic representation "
                                "learning mechanism maps to the research "
                                "question's vision-language alignment "
                                "dimension and can be adapted for video."
                            ),
                        ],
                        "warnings": [],
                    }
                    ]
                )
            ],
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )


def create_provider_response_for_papers(
    papers: tuple[PaperMetadata, ...],
) -> ProviderResponse:
    """Create a valid provider response for the supplied papers."""

    return create_valid_provider_response(
        evaluations=[
            {
                "source_id": f"paper-{index:03d}",
                        "relevance_score": 70,
                "relevance_summary": (
                    f"{paper.title} is relevant."
                ),
                "strengths": [],
                "limitations": [],
                "research_connections": [],
                "warnings": [],
            }
            for index, paper in enumerate(papers, start=1)
        ]
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
        "The paper's semantic representation learning mechanism maps to "
        "the research question's vision-language alignment dimension and "
        "can be adapted for video.",
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


def test_research_evaluation_service_requires_exact_source_ids() -> None:
    """Verify provider instructions preserve source identifier values."""

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

    system_instructions = provider.requests[0].system_instructions

    assert (
        "Treat each source_id as an opaque identifier and return it "
        "exactly as supplied."
        in system_instructions
    )
    assert (
        "Do not modify, expand, normalize, format, or invent "
        "source identifiers."
        in system_instructions
    )


def test_research_evaluation_service_uses_opaque_source_ids() -> None:
    """Verify provider-native identifiers are hidden from evaluation."""

    provider = StubProvider(
        create_valid_provider_response()
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    source_id = "https://openalex.org/W4318566686"
    paper = create_paper_metadata(source_id=source_id)

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert '"source_id": "paper-001"' in (
        provider.requests[0].user_prompt
    )
    assert source_id not in provider.requests[0].user_prompt
    assert result[0].paper == paper


def test_research_evaluation_service_retries_unknown_source_id() -> None:
    """Verify unknown source identifiers trigger one bounded retry."""

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-999"

    provider = SequentialStubProvider(
        (
            invalid_response,
            create_valid_provider_response(),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(result) == 1
    assert len(provider.requests) == 2


def test_research_evaluation_service_retries_missing_evaluation() -> None:
    """Verify incomplete coverage retries only the missing papers."""

    first_paper = create_paper_metadata(
        source_id="paper-001",
        title="First Paper",
    )
    second_paper = create_paper_metadata(
        source_id="paper-002",
        title="Second Paper",
    )

    first_response = create_valid_provider_response(
        evaluations=[
            {
                "source_id": "paper-001",
                "relevance_score": 70,
                "relevance_summary": "First paper is relevant.",
                "strengths": [],
                "limitations": [],
                "research_connections": [
                    "The paper's representation mechanism maps to the "
                    "research question's alignment dimension."
                ],
                "warnings": [],
            },
        ]
    )
    retry_response = create_valid_provider_response(
        evaluations=[
            {
                "source_id": "paper-001",
                "relevance_score": 70,
                "relevance_summary": "Second paper is relevant.",
                "strengths": [],
                "limitations": [],
                "research_connections": [
                    "The paper's representation mechanism maps to the "
                    "research question's alignment dimension."
                ],
                "warnings": [],
            },
        ]
    )

    provider = SequentialStubProvider(
        (
            first_response,
            retry_response,
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
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
    assert len(provider.requests) == 2
    assert [
        request.metadata["paper_count"]
        for request in provider.requests
    ] == [2, 1]
    assert result[0].paper == first_paper
    assert result[1].paper == second_paper

def test_research_evaluation_service_merges_missing_retry_in_order() -> None:
    """Verify retained and retried evaluations preserve paper order."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 4)
    )

    provider = SequentialStubProvider(
        (create_provider_response_for_papers(papers),)
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert tuple(
        evaluation.paper
        for evaluation in result
    ) == papers
    assert [
        request.metadata["paper_count"]
        for request in provider.requests
    ] == [3]



def test_research_evaluation_service_stops_after_one_retry() -> None:
    """Verify persistent traceability failure becomes an unscored result."""

    first_response = create_valid_provider_response()
    first_response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-999"

    second_response = create_valid_provider_response()
    second_response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-998"

    provider = SequentialStubProvider(
        (
            first_response,
            second_response,
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(provider.requests) == 2
    assert result[0].relevance_score is None
    assert result[0].warnings == (
        "Excluded from scoring after an invalid evaluation response.",
    )


@pytest.mark.parametrize(
    ("mechanism_match", "raw_score", "expected_score"),
    (
        ("direct", 74, 0.75),
        ("transferable", 49, 0.50),
        ("transferable", 75, 0.74),
        ("adjacent", 24, 0.25),
        ("adjacent", 50, 0.49),
        ("none", 25, 0.24),
    ),
)
def test_research_evaluation_service_recovers_one_point_boundary_after_retry(
    mechanism_match: str,
    raw_score: int,
    expected_score: float,
) -> None:
    """Only exact neighboring-band scores recover after normal retry."""

    responses = []
    for _ in range(2):
        response = create_valid_provider_response()
        response.structured_output["evaluations"][0].update(
            {
                "relevance_score": raw_score,
                "mechanism_match": mechanism_match,
            }
        )
        responses.append(response)
    provider = SequentialStubProvider(tuple(responses))
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(provider.requests) == 2
    assert result[0].relevance_score == expected_score
    assert result[0].mechanism_match.value == mechanism_match
    assert len(result[0].warnings) == 1
    assert "Relevance score corrected" in result[0].warnings[0]
    assert "after retry" in result[0].warnings[0]


def test_research_evaluation_service_rejects_large_boundary_disagreement() -> None:
    """A material score/mechanism contradiction remains unscored."""

    responses = []
    for _ in range(2):
        response = create_valid_provider_response()
        response.structured_output["evaluations"][0].update(
            {
                "relevance_score": 85,
                "mechanism_match": "transferable",
            }
        )
        responses.append(response)
    provider = SequentialStubProvider(tuple(responses))

    result = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score is None
    assert result[0].warnings == (
        "Excluded from scoring after an invalid evaluation response.",
    )


def test_boundary_recovery_preserves_guidance_seed_provenance() -> None:
    """Boundary correction does not replace candidate provenance."""

    responses = []
    for _ in range(2):
        response = create_valid_provider_response()
        response.structured_output["evaluations"][0].update(
            {
                "relevance_score": 75,
                "mechanism_match": "transferable",
            }
        )
        responses.append(response)
    paper = create_paper_metadata()
    paper = PaperMetadata(
        source_reference=ResearchSourceReference(
            source_name="arxiv",
            source_id="https://arxiv.org/abs/2405.19009",
            title=paper.title,
            is_guidance_seed=True,
            guidance_relevance=ResearchGuidanceRelevance.HIGH,
        ),
        title=paper.title,
        abstract=paper.abstract,
        evidence_status=ResearchPaperEvidenceStatus.AVAILABLE,
    )

    result = ResearchEvaluationService(
        provider=SequentialStubProvider(tuple(responses)),
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].paper.source_reference.is_guidance_seed is True
    assert (
        result[0].paper.source_reference.guidance_relevance
        is ResearchGuidanceRelevance.HIGH
    )
    assert result[0].relevance_score == 0.74


def test_research_evaluation_service_continues_after_invalid_batch() -> None:
    """A persistently malformed batch does not prevent later evaluation."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"source-{index}",
            title=f"Paper {index}",
        )
        for index in range(1, 7)
    )
    invalid_first = create_provider_response_for_papers(papers[:3])
    invalid_first.structured_output["evaluations"][0][
        "source_id"
    ] = "1234567890"
    invalid_retry = create_valid_provider_response(
        evaluations=[
            {
                "source_id": "1234567890",
                "relevance_score": 90,
                "relevance_summary": "Invalid identifier.",
                "strengths": [],
                "limitations": [],
                "research_connections": [],
                "warnings": [],
            }
        ]
    )
    valid_second = create_provider_response_for_papers(papers[3:])
    provider = SequentialStubProvider(
        (invalid_first, invalid_retry, valid_second)
    )

    result = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert len(provider.requests) == 3
    assert result[0].relevance_score is None
    assert result[1].relevance_score == 0.7
    assert result[2].relevance_score == 0.7
    assert tuple(
        evaluation.relevance_score
        for evaluation in result[3:]
    ) == (0.7, 0.7, 0.7)


def test_research_evaluation_service_batches_six_papers() -> None:
    """Verify six papers are evaluated in two bounded provider calls."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 7)
    )

    provider = SequentialStubProvider(
        (
            create_provider_response_for_papers(papers[:3]),
            create_provider_response_for_papers(papers[3:]),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert len(result) == 6
    assert len(provider.requests) == 2
    assert [
        request.metadata["paper_count"]
        for request in provider.requests
    ] == [3, 3]


def test_research_evaluation_service_batches_eleven_papers() -> None:
    """Verify eleven papers are evaluated in bounded provider calls."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 12)
    )

    provider = SequentialStubProvider(
        (
            create_provider_response_for_papers(papers[:3]),
            create_provider_response_for_papers(papers[3:6]),
            create_provider_response_for_papers(papers[6:9]),
            create_provider_response_for_papers(papers[9:]),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert len(result) == 11
    assert len(provider.requests) == 4
    assert [
        request.metadata["paper_count"]
        for request in provider.requests
    ] == [3, 3, 3, 2]


def test_research_evaluation_service_preserves_order_across_batches() -> None:
    """Verify combined evaluations preserve original paper ordering."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 7)
    )

    provider = SequentialStubProvider(
        (
            create_provider_response_for_papers(papers[:3]),
            create_provider_response_for_papers(papers[3:]),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert tuple(
        evaluation.paper
        for evaluation in result
    ) == papers


def test_research_evaluation_service_retries_only_failed_batch() -> None:
    """Verify one failed batch retries without repeating prior batches."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 7)
    )

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-999"

    provider = SequentialStubProvider(
        (
            create_provider_response_for_papers(papers[:3]),
            invalid_response,
            create_provider_response_for_papers(papers[3:]),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert len(result) == 6
    assert len(provider.requests) == 3
    assert [
        request.metadata["paper_count"]
        for request in provider.requests
    ] == [3, 3, 3]


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

    provider = SequentialStubProvider(
        (create_provider_response_for_papers(
            (first_paper, second_paper),
        ),)
    )

    service = ResearchEvaluationService(
        provider=provider,
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


def test_research_evaluation_service_normalizes_integer_score() -> None:
    """Verify integer relevance scores are normalized to 0.0-1.0."""

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


def test_research_evaluation_service_normalizes_score_boundaries() -> None:
    """Verify 0 and 100 map to the supported relevance boundaries."""

    paper = create_paper_metadata()

    for raw_score, expected_score in (
        (0, 0.0),
        (100, 1.0),
    ):
        response = create_valid_provider_response()
        response.structured_output[
            "evaluations"
        ][0]["relevance_score"] = raw_score
        response.structured_output[
            "evaluations"
        ][0]["mechanism_match"] = (
            "direct" if raw_score == 100 else "none"
        )

        service = ResearchEvaluationService(
            provider=StubProvider(response),
            model_name="qwen3:8b",
        )

        result = service.evaluate(
            create_research_request(),
            create_research_strategy(),
            (paper,),
        )

        assert result[0].relevance_score == expected_score


def test_research_evaluation_service_preserves_score_ordering() -> None:
    """Verify 0-100 relevance ordering is preserved after normalization."""

    papers = tuple(
        create_paper_metadata(
            source_id=f"paper-{index:03d}",
            title=f"Paper {index}",
        )
        for index in range(1, 6)
    )
    raw_scores = (90, 75, 50, 25, 0)

    provider = SequentialStubProvider(
        tuple(
            create_valid_provider_response(
                evaluations=[
                    {
                        "source_id": f"paper-{index:03d}",
                        "relevance_score": raw_score,
                        "relevance_summary": f"{paper.title} relevance.",
                        "strengths": [],
                        "limitations": [],
                        "research_connections": [
                            "The paper's representation mechanism maps to "
                            "the research question's alignment dimension."
                        ],
                        "warnings": [],
                    }
                    for index, (paper, raw_score) in enumerate(
                        zip(batch, batch_scores),
                        start=1,
                    )
                ]
            )
            for batch, batch_scores in (
                (papers[:3], raw_scores[:3]),
                (papers[3:], raw_scores[3:]),
            )
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert tuple(
        evaluation.relevance_score
        for evaluation in result
    ) == (
        0.90,
        0.75,
        0.50,
        0.25,
        0.00,
    )


def test_research_evaluation_service_normalizes_one_as_one_percent() -> None:
    """Verify raw score 1 normalizes to 0.01 instead of 1.0."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 1
    response.structured_output[
        "evaluations"
    ][0]["mechanism_match"] = "none"

    service = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.01


def test_research_evaluation_service_normalizes_integral_float_score() -> None:
    """Verify integral float relevance scores are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 95.0

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


def test_research_evaluation_service_rejects_non_integer_score() -> None:
    """Verify provider relevance scores must use the 0-100 integer scale."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 0.95

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
            "Relevance score must be an integer from 0 to 100 or null."
        )
    else:
        raise AssertionError("Expected non-integer relevance failure.")


def test_research_evaluation_service_instructs_relevance_rubric() -> None:
    """Verify provider instructions define the 0-100 relevance rubric."""

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

    system_instructions = provider.requests[0].system_instructions

    assert (
        "Assign relevance_score as an integer from 0 to 100"
        in system_instructions
    )
    assert (
        "Missing or limited metadata must reduce confidence"
        in system_instructions
    )
    assert (
        "directly addresses both the primary application or task and "
        "the central technical problem"
        in system_instructions
    )
    assert (
        "Do not assign a high score based primarily on keyword or "
        "topical overlap."
        in system_instructions
    )
    assert (
        "neither a major dimension nor a concrete transfer path is present"
        in system_instructions
    )
    assert (
        "Use the same relevance standard for every paper in the batch"
        in system_instructions
    )


def test_research_evaluation_service_supplies_guidance_provenance() -> None:
    """Paper-specific seed designation reaches the evaluation request."""

    provider = StubProvider(create_valid_provider_response())
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )
    paper = create_paper_metadata()
    paper = PaperMetadata(
        source_reference=ResearchSourceReference(
            source_name=paper.source_reference.source_name,
            source_id=paper.source_reference.source_id,
            title=paper.source_reference.title,
            is_guidance_seed=True,
            guidance_relevance=ResearchGuidanceRelevance.HIGH,
        ),
        title=paper.title,
        abstract=paper.abstract,
        evidence_status=ResearchPaperEvidenceStatus.AVAILABLE,
    )

    service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    payload = provider.requests[0].user_prompt
    assert '"is_guidance_seed": true' in payload
    assert '"guidance_relevance": "high"' in payload
    instructions = provider.requests[0].system_instructions
    assert "provenance/context only" in instructions
    assert "must not force mechanism_match" in instructions


def test_research_evaluation_service_instructs_transferability_rubric() -> None:
    """Verify concrete cross-domain transfer can receive a strong score."""

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

    system_instructions = provider.requests[0].system_instructions

    assert (
        "provides a concrete, metadata-supported transfer path from a "
        "different application, task, or modality"
        in system_instructions
    )
    assert (
        "a different application, task, or modality must not by itself "
        "cap relevance below 75"
        in system_instructions
    )
    assert (
        "research_connections must identify the paper's source mechanism, "
        "the corresponding dimension of the research question, and any "
        "adaptation needed"
        in system_instructions
    )
    assert (
        "If the supplied metadata cannot support that mapping, assign a "
        "score below 50."
        in system_instructions
    )
    assert (
        "For every score of 75 or higher, state that complete "
        "mechanism-to-question mapping explicitly in "
        "research_connections."
        in system_instructions
    )


def test_research_evaluation_service_calibrates_teacher_alignment() -> None:
    """Mechanism equivalence outranks literal architecture terminology."""

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

    system_instructions = provider.requests[0].system_instructions

    assert (
        "Evaluate the central technical mechanism before literal task, "
        "dataset, or model name overlap."
        in system_instructions
    )
    assert (
        "training a student visual or video encoder to match token-level "
        "or feature-level targets from a frozen vision-language teacher"
        in system_instructions
    )
    assert (
        "do not classify such a paper as background merely because it uses "
        "terms such as ViT, masked modeling, teacher-student learning, or "
        "distillation instead of autoencoder"
        in system_instructions
    )
    assert (
        "mechanism directly to video addresses a major technical dimension "
        "and ordinarily belongs in the 75-89 band"
        in system_instructions
    )
    assert (
        "demonstrated only on images ordinarily belongs in the 50-74 band"
        in system_instructions
    )
    assert (
        "explicit seed status or user preference as a request for careful "
        "evaluation, not as evidence"
        in system_instructions
    )


def test_research_evaluation_service_retries_contradictory_high_score() -> None:
    """Verify a high score without a transfer path is retried once."""

    contradictory_response = create_valid_provider_response()
    contradictory_response.structured_output[
        "evaluations"
    ][0].update(
        {
            "relevance_score": 76,
            "relevance_summary": (
                "The paper is related, but no concrete transfer path is "
                "provided by the supplied metadata."
            ),
            "research_connections": [
                "The paper shares broad alignment terminology."
            ],
            "mechanism_match": "direct",
        }
    )
    corrected_response = create_valid_provider_response()
    corrected_response.structured_output[
        "evaluations"
    ][0].update(
        {
            "relevance_score": 74,
            "relevance_summary": (
                "The paper uses a related alignment mechanism, but the "
                "transfer path remains incomplete."
            ),
            "research_connections": [
                "The alignment mechanism is related to the research "
                "question's shared-representation dimension."
            ],
            "mechanism_match": "transferable",
        }
    )

    provider = SequentialStubProvider(
        (
            contradictory_response,
            corrected_response,
        )
    )
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.74
    assert len(provider.requests) == 2


def test_research_evaluation_service_accepts_supported_high_score() -> None:
    """Verify a concrete mechanism-to-question mapping supports 75+."""

    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 76,
            "research_connections": [
                "The paper's token-alignment mechanism maps to the "
                "research question's shared-representation dimension and "
                "can be adapted to temporal video features."
            ],
        }
    )
    provider = StubProvider(response)
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert result[0].relevance_score == 0.76
    assert len(provider.requests) == 1


def test_research_evaluation_service_logs_structured_decision(caplog) -> None:
    """DEBUG output exposes the complete model relevance decision."""

    caplog.set_level(
        logging.DEBUG,
        logger=(
            "project0.agents.research.research_evaluation_service"
        ),
    )
    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 82,
            "mechanism_match": "direct",
            "source_mechanism": "Frozen CLIP token distillation.",
            "target_problem_dimension": "Video semantic alignment.",
            "required_adaptation": "Use the target video encoder.",
            "evidence_support": [
                "The abstract describes a frozen CLIP teacher."
            ],
        }
    )

    ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (
            create_paper_metadata(
                source_id="arxiv:2303.16058",
                title="Unmasked Teacher",
            ),
        ),
    )

    trace = next(
        record.getMessage()
        for record in caplog.records
        if "Research evaluation trace:" in record.getMessage()
    )
    assert "stage=final" in trace
    assert "attempt=initial" in trace
    assert "paper_source=arxiv:2303.16058" in trace
    assert "title='Unmasked Teacher'" in trace
    assert "mechanism_match=direct" in trace
    assert "relevance_score=0.82" in trace
    assert "source_mechanism='Frozen CLIP token distillation.'" in trace
    assert (
        "target_problem_dimension='How can self-supervised video "
        "representations be improved for VideoQA'"
        in trace
    )
    assert "required_adaptation='Use the target video encoder.'" in trace
    assert "evidence_support=" in trace
    assert "validation_status=valid" in trace


def test_research_evaluation_service_logs_initial_and_retry_decisions(
    caplog,
) -> None:
    """A rejected decision and its corrected retry are both traceable."""

    caplog.set_level(
        logging.DEBUG,
        logger=(
            "project0.agents.research.research_evaluation_service"
        ),
    )
    invalid = create_valid_provider_response()
    invalid.structured_output["evaluations"][0].update(
        {
            "relevance_score": 25,
            "mechanism_match": "direct",
        }
    )
    corrected = create_valid_provider_response()
    corrected.structured_output["evaluations"][0].update(
        {
            "relevance_score": 82,
            "mechanism_match": "direct",
        }
    )

    ResearchEvaluationService(
        provider=SequentialStubProvider((invalid, corrected)),
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(title="Unmasked Teacher"),),
    )

    traces = [
        record.getMessage()
        for record in caplog.records
        if "Research evaluation trace:" in record.getMessage()
    ]
    assert any(
        "attempt=initial" in trace
        and "validation_status=invalid" in trace
        and "mechanism_match=direct" in trace
        and "relevance_score=0.25" in trace
        for trace in traces
    )
    assert any(
        "attempt=retry" in trace
        and "validation_status=valid" in trace
        and "mechanism_match=direct" in trace
        and "relevance_score=0.82" in trace
        for trace in traces
    )


def test_research_evaluation_service_retries_direct_mechanism_scored_adjacent(
) -> None:
    """A recognized direct mechanism cannot remain in the adjacent band."""

    invalid = create_valid_provider_response()
    invalid.structured_output["evaluations"][0].update(
        {
            "relevance_score": 25,
            "mechanism_match": "direct",
            "source_mechanism": (
                "A video encoder matches token targets from a frozen CLIP "
                "teacher through a distillation objective."
            ),
            "target_problem_dimension": (
                "Semantic alignment of learned video representations."
            ),
            "required_adaptation": (
                "Use the project's video encoder as the student."
            ),
            "evidence_support": [
                "The supplied abstract describes a frozen CLIP teacher and "
                "token-level alignment for video representations."
            ],
        }
    )
    corrected = create_valid_provider_response()
    corrected.structured_output["evaluations"][0].update(
        {
            "relevance_score": 82,
            "mechanism_match": "direct",
            "source_mechanism": invalid.structured_output[
                "evaluations"
            ][0]["source_mechanism"],
            "target_problem_dimension": invalid.structured_output[
                "evaluations"
            ][0]["target_problem_dimension"],
            "required_adaptation": invalid.structured_output[
                "evaluations"
            ][0]["required_adaptation"],
            "evidence_support": invalid.structured_output[
                "evaluations"
            ][0]["evidence_support"],
        }
    )

    provider = SequentialStubProvider((invalid, corrected))
    result = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (
            create_paper_metadata(
                source_id="arxiv:2303.16058",
                title="Unmasked Teacher",
            ),
        ),
    )

    assert len(provider.requests) == 2
    assert result[0].relevance_score == 0.82
    assert result[0].mechanism_match is ResearchMechanismMatch.DIRECT


def test_research_evaluation_service_preserves_structured_benchmark_bands(
) -> None:
    """Positive and control papers retain mechanism-consistent ordering."""

    papers = (
        create_paper_metadata(title="Unmasked Teacher"),
        create_paper_metadata(title="Unmasked Token Alignment"),
        create_paper_metadata(title="SemiCLIP"),
    )
    response = create_valid_provider_response(
        evaluations=[
            {
                "source_id": "paper-001",
                "relevance_score": 84,
                "relevance_summary": "Direct video teacher alignment.",
                "strengths": [],
                "limitations": [],
                "research_connections": ["Direct video mechanism."],
                "warnings": [],
                "mechanism_match": "direct",
                "source_mechanism": "Frozen CLIP token distillation.",
                "target_problem_dimension": "Video semantic alignment.",
                "required_adaptation": "Use the target video encoder.",
                "evidence_support": ["The mechanism is demonstrated on video."],
            },
            {
                "source_id": "paper-002",
                "relevance_score": 68,
                "relevance_summary": "Transferable image teacher alignment.",
                "strengths": [],
                "limitations": [],
                "research_connections": ["Transfer image alignment to video."],
                "warnings": [],
                "mechanism_match": "transferable",
                "source_mechanism": "Frozen CLIP token alignment.",
                "target_problem_dimension": "Video semantic alignment.",
                "required_adaptation": "Extend token alignment across frames.",
                "evidence_support": ["The mechanism is demonstrated on images."],
            },
            {
                "source_id": "paper-003",
                "relevance_score": 40,
                "relevance_summary": "Adjacent general CLIP adaptation.",
                "strengths": [],
                "limitations": [],
                "research_connections": ["Provides background only."],
                "warnings": [],
                "mechanism_match": "adjacent",
                "source_mechanism": "Generic CLIP consistency training.",
                "target_problem_dimension": "Broad multimodal robustness.",
                "required_adaptation": "No concrete video transfer is shown.",
                "evidence_support": ["The abstract discusses CLIP adaptation."],
            },
        ]
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    assert tuple(item.relevance_score for item in result) == (
        0.84,
        0.68,
        0.40,
    )
    assert tuple(item.mechanism_match for item in result) == (
        ResearchMechanismMatch.DIRECT,
        ResearchMechanismMatch.TRANSFERABLE,
        ResearchMechanismMatch.ADJACENT,
    )


def test_target_problem_dimension_is_request_scoped_across_batch() -> None:
    """One paper's task cannot replace another paper's target dimension."""

    papers = (
        create_paper_metadata(title="Masked Video Distillation"),
        create_paper_metadata(title="VATT"),
        create_paper_metadata(title="Time-Contrastive Networks"),
    )
    contaminated_dimensions = (
        "sequential decision making",
        "zero-shot transfer and fully-supervised learning",
        "robot imitation learning",
    )
    response = create_valid_provider_response(
        evaluations=[
            {
                "source_id": f"paper-{index:03d}",
                "relevance_score": 24,
                "relevance_summary": "Provider response.",
                "strengths": [],
                "limitations": [],
                "research_connections": [],
                "warnings": [],
                "mechanism_match": "none",
                "source_mechanism": "Provider mechanism.",
                "target_problem_dimension": contaminated_dimension,
                "required_adaptation": "Provider adaptation.",
                "evidence_support": [],
            }
            for index, contaminated_dimension in enumerate(
                contaminated_dimensions,
                start=1,
            )
        ]
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        papers,
    )

    expected = (
        "How can self-supervised video representations be improved for "
        "VideoQA"
    )
    assert {item.target_problem_dimension for item in result} == {expected}


def test_provider_request_constrains_target_problem_dimension() -> None:
    """Strict output schema exposes one immutable request-scoped target."""

    provider = StubProvider(create_valid_provider_response())
    ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    ).evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    expected = (
        "How can self-supervised video representations be improved for "
        "VideoQA"
    )
    payload = __import__("json").loads(provider.requests[0].user_prompt)
    target_schema = provider.requests[0].response_schema["properties"][
        "evaluations"
    ]["items"]["properties"]["target_problem_dimension"]
    assert payload["target_problem_dimension"] == expected
    assert target_schema["const"] == expected
    assert "immutable request-scoped value" in (
        provider.requests[0].system_instructions
    )


def test_research_evaluation_service_corrects_video_teacher_alignment(
) -> None:
    """Explicit video teacher-token alignment cannot remain none."""

    paper = create_paper_metadata(title="Video Foundation Model")
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        abstract=(
            "We train a video encoder from scratch by aligning unmasked "
            "video tokens with an image foundation model that serves as "
            "the teacher. Semantic guidance produces multimodal-friendly "
            "video representations."
        ),
    )
    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 24,
            "mechanism_match": "none",
            "source_mechanism": "",
            "target_problem_dimension": "",
            "required_adaptation": "",
            "evidence_support": [],
        }
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).rank_candidates(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].mechanism_match is ResearchMechanismMatch.DIRECT
    assert result[0].relevance_score == 0.75
    assert result[0].source_mechanism
    assert result[0].target_problem_dimension
    assert result[0].required_adaptation
    assert result[0].evidence_support
    assert "corrected deterministically" in result[0].warnings[-1]


def test_research_evaluation_service_corrects_image_clip_token_alignment(
) -> None:
    """Image-only frozen-CLIP token alignment is transferable."""

    paper = create_paper_metadata(title="Visual Token Alignment")
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        abstract=(
            "The method trains a Vision Transformer from scratch by "
            "aligning unmasked visual tokens with corresponding image "
            "tokens from a frozen CLIP vision encoder. The ViT model is "
            "automatically aligned with the CLIP text encoder."
        ),
    )
    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 24,
            "mechanism_match": "none",
            "limitations": [
                (
                    "Does not address the research question of aligning "
                    "video representations with frozen CLIP."
                ),
                "The image-only method still requires video validation.",
            ],
            "research_connections": [
                (
                    "The paper is off-topic and does not provide any "
                    "alignment mechanism."
                ),
            ],
            "source_mechanism": "",
            "target_problem_dimension": "",
            "required_adaptation": "",
            "evidence_support": [],
        }
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).rank_candidates(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].mechanism_match is ResearchMechanismMatch.TRANSFERABLE
    assert result[0].relevance_score == 0.50
    assert "temporally aggregated video" in result[0].required_adaptation
    assert result[0].research_connections == (
        "Deterministic evidence screening maps the paper to the "
        "transferable mechanism band.",
    )
    assert result[0].limitations == (
        "The image-only method still requires video validation.",
    )


def test_research_evaluation_service_corrects_clip_latent_autoencoder_band(
) -> None:
    """Image autoencoder alignment belongs in the transferable band."""

    paper = create_paper_metadata(title="Context Autoencoder")
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        abstract=(
            "A context autoencoder uses CLIP latent as the target for "
            "visible latent alignment and masked latent alignment. The "
            "visual encoder learns semantically rich representations."
        ),
    )
    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 50,
            "mechanism_match": "adjacent",
        }
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).rank_candidates(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].mechanism_match is ResearchMechanismMatch.TRANSFERABLE
    assert result[0].relevance_score == 0.50


def test_research_evaluation_service_caps_generic_clip_adaptation(
) -> None:
    """Generic CLIP adaptation lacks a teacher-target mechanism mapping."""

    paper = create_paper_metadata(title="Semi-Supervised CLIP Adaptation")
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        abstract=(
            "Semi-supervised CLIP adaptation uses semantic concept mining "
            "and consistency regularization to improve downstream image "
            "classification and retrieval with limited labeled data."
        ),
    )
    response = create_valid_provider_response()
    response.structured_output["evaluations"][0].update(
        {
            "relevance_score": 50,
            "mechanism_match": "transferable",
        }
    )

    result = ResearchEvaluationService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).rank_candidates(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].mechanism_match is ResearchMechanismMatch.ADJACENT
    assert result[0].relevance_score == 0.49


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


def test_research_evaluation_service_recovers_unknown_source_id() -> None:
    """Verify a persistent unknown identifier becomes unscored."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["source_id"] = "paper-999"

    provider = StubProvider(response)
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(provider.requests) == 2
    assert result[0].relevance_score is None
    assert result[0].warnings == (
        "Excluded from scoring after an invalid evaluation response.",
    )


def test_research_evaluation_service_recovers_duplicate_source_id() -> None:
    """Verify duplicate identifiers preserve the first valid evaluation."""

    duplicate = create_valid_provider_response().structured_output[
        "evaluations"
    ][0]

    response = create_valid_provider_response(
        evaluations=[
            duplicate,
            duplicate.copy(),
        ]
    )

    provider = StubProvider(response)
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (create_paper_metadata(),),
    )

    assert len(provider.requests) == 1
    assert result[0].relevance_score == 0.95


def test_research_evaluation_service_recovers_missing_paper_evaluation() -> None:
    """Verify a persistently missing paper becomes unscored."""

    first_paper = create_paper_metadata(
        source_id="paper-001",
        title="First Paper",
    )
    second_paper = create_paper_metadata(
        source_id="paper-002",
        title="Second Paper",
    )

    provider = SequentialStubProvider(
        (
            create_valid_provider_response(),
            create_valid_provider_response(
                evaluations=[]
            ),
            create_valid_provider_response(
                evaluations=[]
            ),
        )
    )

    service = ResearchEvaluationService(
        provider=provider,
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

    assert len(provider.requests) == 2
    assert tuple(evaluation.paper for evaluation in result) == (
        first_paper,
        second_paper,
    )
    assert result[0].relevance_score == 0.95
    assert result[1].relevance_score is None
    assert result[1].warnings == (
        "Excluded from scoring after an invalid evaluation response.",
    )


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
            "Relevance score must be an integer from 0 to 100 or null."
        )
    else:
        raise AssertionError("Expected invalid relevance score failure.")


def test_research_evaluation_service_rejects_out_of_range_score() -> None:
    """Verify relevance score must be within supported range."""

    response = create_valid_provider_response()
    response.structured_output[
        "evaluations"
    ][0]["relevance_score"] = 101

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
            "Relevance score must be between 0 and 100."
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


def test_research_evaluation_service_does_not_score_discovery_only_paper() -> None:
    """Discovery-only metadata bypasses unsupported model scoring."""

    paper = create_paper_metadata()
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        evidence_status=ResearchPaperEvidenceStatus.DISCOVERY_ONLY,
    )
    provider = StubProvider(create_valid_provider_response())
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.evaluate(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].relevance_score is None
    assert "Discovery-only candidate" in result[0].relevance_summary
    assert result[0].warnings == (
        "Excluded from evidence-based scoring.",
    )
    assert provider.requests == []


def test_research_evaluation_service_ranks_pre_acquisition_metadata() -> None:
    """Preliminary ranking does not treat evidence status as final."""

    paper = create_paper_metadata()
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        evidence_status=ResearchPaperEvidenceStatus.DISCOVERY_ONLY,
    )
    provider = StubProvider(create_valid_provider_response())
    service = ResearchEvaluationService(
        provider=provider,
        model_name="qwen3:8b",
    )

    result = service.rank_candidates(
        create_research_request(),
        create_research_strategy(),
        (paper,),
    )

    assert result[0].relevance_score == 0.95
    assert len(provider.requests) == 1
    payload = __import__("json").loads(provider.requests[0].user_prompt)
    assert payload["evaluation_stage"] == "preliminary_metadata_ranking"
    assert payload["papers"][0]["evidence_status"] == "pending_acquisition"
    assert (
        "Do not treat the current evidence_status as a final discovery-only "
        "decision."
        in provider.requests[0].system_instructions
    )
