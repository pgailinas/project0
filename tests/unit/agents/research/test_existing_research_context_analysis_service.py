# ============================================================
# Project0 - Existing Research Context Analysis Service Tests
#
# File: test_existing_research_context_analysis_service.py
#
# Purpose:
#     Verify existing research context reasoning orchestration,
#     structured output parsing, provenance, and failure behavior.
#
# ============================================================

from __future__ import annotations

import json

import pytest

from project0.agents.research.existing_research_context_analysis_service import (
    ExistingResearchContextAnalysisService,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    ResearchContextDocument,
    ResearchContextDocumentType,
    ResearchContextExtractionStatus,
    ResearchEvidenceSourceType,
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


def create_context_document() -> ResearchContextDocument:
    """Create a representative normalized research context document."""

    return ResearchContextDocument(
        source_name="ece551_part1.md",
        document_type=ResearchContextDocumentType.MARKDOWN,
        extraction_method="utf-8",
        extracted_text=(
            "# Research Problem\n"
            "Video representations lack semantic alignment.\n\n"
            "# Findings\n"
            "Reconstruction quality did not ensure VideoQA quality.\n\n"
            "# Limitations\n"
            "The fusion approach did not resolve semantic alignment.\n"
        ),
        extraction_status=ResearchContextExtractionStatus.COMPLETED,
        document_id="context-001",
    )


def create_valid_provider_response() -> ProviderResponse:
    """Create a valid structured provider response."""

    return ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output={
            "research_problem": {
                "content": (
                    "Video representations lack semantic alignment."
                ),
                "section": "Research Problem",
            },
            "prior_work": [
                {
                    "content": (
                        "The project evaluated reconstruction-based "
                        "video representations."
                    ),
                    "section": "Prior Work",
                },
            ],
            "implemented_approaches": [
                {
                    "content": (
                        "A fusion-based approach was implemented."
                    ),
                    "section": "Methods",
                },
            ],
            "findings": [
                {
                    "content": (
                        "Reconstruction quality did not ensure "
                        "VideoQA quality."
                    ),
                    "section": "Findings",
                },
            ],
            "limitations": [
                {
                    "content": (
                        "The fusion approach did not resolve "
                        "semantic alignment."
                    ),
                    "section": "Limitations",
                },
            ],
            "unresolved_questions": [
                {
                    "content": (
                        "How should video and text representations "
                        "be aligned?"
                    ),
                    "section": None,
                },
            ],
            "stated_future_work": [
                {
                    "content": (
                        "Future work should investigate semantic "
                        "alignment."
                    ),
                    "section": "Conclusion",
                },
            ],
            "inferred_solution_search_concepts": [
                {
                    "source_representation": "autoencoder video features",
                    "target_model_or_space": "frozen CLIP",
                    "solution_mechanism": "feature distillation",
                },
                {
                    "source_representation": "autoencoder video tokens",
                    "target_model_or_space": "frozen CLIP",
                    "solution_mechanism": "token alignment",
                },
                {
                    "source_representation": "autoencoder representations",
                    "target_model_or_space": "CLIP space",
                    "solution_mechanism": "contrastive projection",
                },
            ],
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )


def test_context_analysis_service_creates_structured_context() -> None:
    """Verify successful existing research context creation."""

    document = create_context_document()
    provider = StubProvider(
        create_valid_provider_response()
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(document)

    assert result.research_problem is not None
    assert result.research_problem.content == (
        "Video representations lack semantic alignment."
    )
    assert len(result.prior_work) == 1
    assert len(result.implemented_approaches) == 1
    assert len(result.findings) == 1
    assert len(result.limitations) == 1
    assert len(result.unresolved_questions) == 1
    assert len(result.stated_future_work) == 1
    assert result.inferred_solution_search_concepts == (
        "autoencoder video features frozen CLIP feature distillation",
        "autoencoder video tokens frozen CLIP token alignment",
        "autoencoder representations CLIP space contrastive projection",
    )


def test_context_analysis_service_constructs_context_provenance() -> None:
    """Verify context findings receive deterministic provenance."""

    document = create_context_document()
    provider = StubProvider(
        create_valid_provider_response()
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(document)

    assert result.research_problem is not None

    evidence = result.research_problem.evidence[0]

    assert (
        evidence.source_type
        == ResearchEvidenceSourceType.CONTEXT_DOCUMENT
    )
    assert evidence.source_id == document.document_id
    assert evidence.page_number is None
    assert evidence.section == "Research Problem"


def test_context_analysis_service_invokes_provider() -> None:
    """Verify provider orchestration and request metadata."""

    document = create_context_document()
    provider = StubProvider(
        create_valid_provider_response()
    )

    ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(document)

    assert len(provider.requests) == 1

    provider_request = provider.requests[0]

    assert provider_request.model_name == "qwen3:8b"
    assert provider_request.temperature == 0.0
    assert provider_request.metadata[
        "research_context_document_id"
    ] == document.document_id
    assert provider_request.metadata[
        "source_name"
    ] == document.source_name


def test_context_analysis_service_sends_document_content() -> None:
    """Verify normalized document content is supplied to the provider."""

    document = create_context_document()
    provider = StubProvider(
        create_valid_provider_response()
    )

    ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        document,
        research_question=(
            "How should video representations align with CLIP?"
        ),
    )

    user_payload = json.loads(
        provider.requests[0].user_prompt
    )

    assert user_payload["document_id"] == document.document_id
    assert user_payload["source_name"] == document.source_name
    assert user_payload["research_question"] == (
        "How should video representations align with CLIP?"
    )
    assert (
        user_payload["extracted_text"]
        == document.extracted_text
    )


def test_context_analysis_service_requires_source_only_analysis() -> None:
    """Verify provider instructions prohibit unsupported inference."""

    provider = StubProvider(
        create_valid_provider_response()
    )

    ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    system_instructions = provider.requests[0].system_instructions

    assert "Analyze only the supplied document text" in system_instructions
    assert (
        "Do not use outside knowledge to add factual claims about "
        "the document."
        in system_instructions
    )
    assert "Do not invent unsupported claims." in system_instructions
    assert (
        "do not convert your own recommendations into stated "
        "future work."
        in system_instructions
    )
    assert (
        "Return them only in inferred_solution_search_concepts"
        in system_instructions
    )
    assert (
        "do not present them as document findings or stated future "
        "work."
        in system_instructions
    )
    assert "the source representation or model" in system_instructions
    assert "the target model or representation space" in system_instructions
    assert "a technically specific solution mechanism" in system_instructions
    assert "return three separate elements" in system_instructions
    assert "infer exactly three" in system_instructions
    assert "distinct solution mechanism" in system_instructions


def test_context_analysis_service_does_not_request_page_numbers() -> None:
    """Verify unavailable PDF page provenance is not requested."""

    provider = StubProvider(
        create_valid_provider_response()
    )

    ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    provider_request = provider.requests[0]

    assert "page_number" not in json.dumps(
        provider_request.response_schema
    )
    assert (
        "Do not invent page numbers or other unavailable provenance."
        in provider_request.system_instructions
    )


def test_context_analysis_service_supports_missing_research_problem() -> None:
    """Verify unsupported research problem may be returned as null."""

    response = create_valid_provider_response()
    response.structured_output["research_problem"] = None

    result = ExistingResearchContextAnalysisService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    assert result.research_problem is None


def test_context_analysis_service_supports_empty_categories() -> None:
    """Verify unsupported context categories may be empty."""

    response = create_valid_provider_response()

    for field_name in (
        "prior_work",
        "implemented_approaches",
        "findings",
        "limitations",
        "unresolved_questions",
        "stated_future_work",
        "inferred_solution_search_concepts",
    ):
        response.structured_output[field_name] = []

    result = ExistingResearchContextAnalysisService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    assert result.prior_work == ()
    assert result.implemented_approaches == ()
    assert result.findings == ()
    assert result.limitations == ()
    assert result.unresolved_questions == ()
    assert result.stated_future_work == ()
    assert result.inferred_solution_search_concepts == ()


def test_context_analysis_service_accepts_descriptive_concept_component() -> None:
    """Verify descriptive structured components do not fail analysis."""

    response = create_valid_provider_response()
    response.structured_output[
        "inferred_solution_search_concepts"
    ] = [
        {
            "source_representation": "autoencoder generated video representations",
            "target_model_or_space": "frozen CLIP space",
            "solution_mechanism": "feature distillation",
        },
    ]

    provider = StubProvider(response)

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    assert result.inferred_solution_search_concepts == (
        (
            "autoencoder generated video representations frozen CLIP "
            "space feature distillation"
        ),
    )
    assert len(provider.requests) == 1


def test_context_analysis_service_retries_missing_concept_component() -> None:
    """Verify every inferred concept contains all three required elements."""

    response = create_valid_provider_response()
    response.structured_output[
        "inferred_solution_search_concepts"
    ] = [
        {
            "source_representation": "autoencoder video features",
            "target_model_or_space": "frozen CLIP",
        },
    ]
    provider = SequentialStubProvider(
        (response, create_valid_provider_response())
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(create_context_document())

    assert result.inferred_solution_search_concepts[0] == (
        "autoencoder video features frozen CLIP feature distillation"
    )
    assert len(provider.requests) == 2


def test_context_analysis_service_adds_missing_question_model_anchors() -> None:
    """Verify explicit question model names enrich inferred concepts."""

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output[
        "inferred_solution_search_concepts"
    ][0] = {
        "source_representation": "video features",
        "target_model_or_space": "embedding space",
        "solution_mechanism": "feature distillation",
    }
    provider = StubProvider(invalid_response)

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document(),
        research_question=(
            "How can autoencoder video representations align with frozen "
            "CLIP embeddings?"
        ),
    )

    assert result.inferred_solution_search_concepts[0] == (
        "autoencoder CLIP video features embedding space feature distillation"
    )
    assert len(provider.requests) == 1


def test_context_analysis_service_retries_fewer_than_three_concepts() -> None:
    """Verify a submitted question requires three solution concepts."""

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output[
        "inferred_solution_search_concepts"
    ] = invalid_response.structured_output[
        "inferred_solution_search_concepts"
    ][:2]
    provider = SequentialStubProvider(
        (invalid_response, create_valid_provider_response())
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document(),
        research_question=(
            "How can autoencoder video representations align with frozen "
            "CLIP embeddings?"
        ),
    )

    assert len(result.inferred_solution_search_concepts) == 3
    assert len(provider.requests) == 2


def test_context_analysis_service_retries_duplicate_mechanisms() -> None:
    """Verify the three solution concepts use distinct mechanisms."""

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output[
        "inferred_solution_search_concepts"
    ][1]["solution_mechanism"] = "feature distillation"
    provider = SequentialStubProvider(
        (invalid_response, create_valid_provider_response())
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document(),
        research_question=(
            "How can autoencoder video representations align with frozen "
            "CLIP embeddings?"
        ),
    )

    assert len(result.inferred_solution_search_concepts) == 3
    assert len(provider.requests) == 2


def test_context_analysis_service_retries_missing_structured_output() -> None:
    """Verify missing structured output triggers one bounded retry."""

    invalid_response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output=None,
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )

    provider = SequentialStubProvider(
        (
            invalid_response,
            create_valid_provider_response(),
        )
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    assert result.research_problem is not None
    assert len(provider.requests) == 2


def test_context_analysis_service_retries_malformed_finding() -> None:
    """Verify malformed finding structure triggers one bounded retry."""

    invalid_response = create_valid_provider_response()
    invalid_response.structured_output["findings"] = [
        {
            "content": "",
            "section": "Findings",
        },
    ]

    provider = SequentialStubProvider(
        (
            invalid_response,
            create_valid_provider_response(),
        )
    )

    result = ExistingResearchContextAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_context_document()
    )

    assert len(result.findings) == 1
    assert len(provider.requests) == 2


def test_context_analysis_service_stops_after_one_retry() -> None:
    """Verify a second structured-output failure is returned."""

    first_response = create_valid_provider_response()
    first_response.structured_output["limitations"] = "invalid"

    second_response = create_valid_provider_response()
    second_response.structured_output["limitations"] = "invalid"

    provider = SequentialStubProvider(
        (
            first_response,
            second_response,
        )
    )

    with pytest.raises(
        ValueError,
        match="limitations",
    ):
        ExistingResearchContextAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_context_document()
        )

    assert len(provider.requests) == 2


def test_context_analysis_service_propagates_provider_error() -> None:
    """Verify provider failures are not silently retried."""

    provider = StubProvider(
        create_valid_provider_response(),
        error=RuntimeError("Provider unavailable."),
    )

    with pytest.raises(
        RuntimeError,
        match="Provider unavailable",
    ):
        ExistingResearchContextAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_context_document()
        )

    assert len(provider.requests) == 1


def test_context_analysis_service_rejects_non_array_category() -> None:
    """Verify category fields must be arrays."""

    response = create_valid_provider_response()
    response.structured_output["prior_work"] = {
        "content": "Invalid structure.",
        "section": None,
    }

    provider = SequentialStubProvider(
        (
            response,
            response,
        )
    )

    with pytest.raises(
        ValueError,
        match="prior_work",
    ):
        ExistingResearchContextAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_context_document()
        )


def test_context_analysis_service_rejects_invalid_section_type() -> None:
    """Verify finding section provenance must be string or null."""

    response = create_valid_provider_response()
    response.structured_output["findings"][0]["section"] = 42

    provider = SequentialStubProvider(
        (
            response,
            response,
        )
    )

    with pytest.raises(
        ValueError,
        match="section",
    ):
        ExistingResearchContextAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_context_document()
        )
