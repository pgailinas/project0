# ============================================================
# Project0 - Paper Analysis Service Tests
#
# File: test_paper_analysis_service.py
#
# Purpose:
#     Verify retained-paper reasoning orchestration,
#     metadata/abstract grounding, and failure behavior.
#
# ============================================================

from __future__ import annotations

import json

import pytest

from project0.agents.research.paper_analysis_service import (
    PaperAnalysisService,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchEvidenceSourceType,
    ResearchPaperAnalysisBasis,
    ResearchPaperEvidenceSection,
    ResearchPaperEvidenceStatus,
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


class SequentialStubProvider:
    """Provide deterministic sequential responses for testing."""

    def __init__(
        self,
        responses: tuple[ProviderResponse, ...],
    ) -> None:
        """Initialize configured sequential provider responses."""

        self.responses = responses
        self.requests: list[ProviderRequest] = []

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Return the next configured provider response."""

        self.requests.append(request)

        return self.responses[len(self.requests) - 1]


def create_request() -> ResearchRequest:
    """Create a representative research request."""

    return ResearchRequest(
        question=(
            "How should video representations be aligned with "
            "vision-language semantic spaces for VideoQA?"
        ),
        guidance="Focus on semantic alignment.",
    )


def create_strategy() -> ResearchStrategy:
    """Create a representative research strategy."""

    return ResearchStrategy(
        concepts=(
            "video representation learning",
            "vision-language alignment",
        ),
        search_terms=(
            "video representation vision-language alignment",
        ),
    )


def create_paper(
    source_id: str = "paper-001",
    title: str = "Example Alignment Paper",
) -> PaperMetadata:
    """Create retained paper metadata."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id=source_id,
        title=title,
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
        source_url="https://example.test/paper",
    )

    return PaperMetadata(
        source_reference=reference,
        title=title,
        authors=reference.authors,
        publication_year=2024,
        abstract=(
            "The paper aligns video and text representations "
            "using a contrastive objective."
        ),
        venue="Example Conference",
        source_url=reference.source_url,
    )


def create_valid_response() -> ProviderResponse:
    """Create a valid structured paper analysis response."""

    def finding(content: str) -> dict:
        return {
            "content": content,
            "section": None,
        }

    return ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output={
            "problem": finding(
                "The paper studies semantic alignment."
            ),
            "approach": finding(
                "The paper uses contrastive representation learning."
            ),
            "representations": [
                finding(
                    "Video and language embeddings are aligned."
                ),
            ],
            "modalities": [
                finding(
                    "The method uses video and text."
                ),
            ],
            "learning_objectives": [
                finding(
                    "A contrastive objective provides alignment."
                ),
            ],
            "datasets_tasks": [],
            "findings": [
                finding(
                    "The representation supports semantic comparison."
                ),
            ],
            "limitations": [],
            "warnings": [],
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )


def test_metadata_analysis_creates_structured_analysis() -> None:
    """Verify metadata/abstract paper analysis creation."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response()
    )

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )

    assert len(result) == 1

    analysis = result[0]

    assert analysis.paper is paper
    assert (
        analysis.analysis_basis
        == ResearchPaperAnalysisBasis.ABSTRACT_METADATA
    )
    assert analysis.problem.content == (
        "The paper studies semantic alignment."
    )
    assert analysis.approach.content == (
        "The paper uses contrastive representation learning."
    )
    assert len(analysis.representations) == 1
    assert len(analysis.modalities) == 1
    assert len(analysis.learning_objectives) == 1
    assert analysis.datasets_tasks == ()
    assert len(analysis.findings) == 1
    assert analysis.limitations == ()
    assert analysis.warnings == ()


def test_metadata_analysis_constructs_paper_provenance() -> None:
    """Verify findings retain authoritative paper provenance."""

    paper = create_paper()

    analysis = PaperAnalysisService(
        provider=StubProvider(
            create_valid_response()
        ),
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )[0]

    evidence = analysis.approach.evidence[0]

    assert (
        evidence.source_type
        == ResearchEvidenceSourceType.RESEARCH_PAPER
    )
    assert evidence.source_id == "paper-001"
    assert evidence.page_number is None
    assert evidence.section == "Abstract"


def test_metadata_request_supplies_abstract_without_full_text() -> None:
    """Verify paper analysis supplies metadata and abstract only."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response()
    )

    PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )

    payload = json.loads(
        provider.requests[0].user_prompt
    )

    assert payload["paper"]["source_id"] == "paper-001"
    assert payload["paper"]["analysis_basis"] == "abstract_metadata"
    assert payload["paper"]["abstract"] == paper.abstract
    assert "research_question" not in payload
    assert "guidance" not in payload
    assert "research_concepts" not in payload
    assert "pages" not in payload["paper"]
    assert "document_id" not in payload["paper"]


def test_response_schema_does_not_request_page_provenance() -> None:
    """Verify provider output has no full-document provenance fields."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response()
    )

    PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )

    finding_schema = (
        provider.requests[0]
        .response_schema["properties"]["problem"]
    )

    assert "evidence_ids" not in finding_schema["properties"]
    assert "page_numbers" not in finding_schema["properties"]


def test_response_schema_does_not_require_source_id() -> None:
    """Verify paper identity is not delegated to provider output."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response()
    )

    PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )

    response_schema = provider.requests[0].response_schema

    assert "source_id" not in response_schema["properties"]
    assert "source_id" not in response_schema["required"]
    assert "research_relevance" not in response_schema["properties"]
    assert "research_relevance" not in response_schema["required"]


def test_missing_structured_output_retries_once() -> None:
    """Verify missing structured output triggers one bounded retry."""

    invalid_response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output=None,
    )

    provider = SequentialStubProvider(
        (
            invalid_response,
            create_valid_response(),
        )
    )

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (create_paper(),),
    )

    assert len(result) == 1
    assert len(provider.requests) == 2


def test_provider_error_propagates_without_retry() -> None:
    """Verify provider failures propagate to workflow handling."""

    provider = StubProvider(
        create_valid_response(),
        error=RuntimeError("Provider unavailable."),
    )

    with pytest.raises(
        RuntimeError,
        match="Provider unavailable",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (create_paper(),),
        )

    assert len(provider.requests) == 1


def test_multiple_papers_preserve_retained_order() -> None:
    """Verify paper analyses preserve retained-paper ordering."""

    first = create_paper(
        source_id="paper-001",
        title="First Paper",
    )
    second = create_paper(
        source_id="paper-002",
        title="Second Paper",
    )

    provider = SequentialStubProvider(
        (
            create_valid_response(),
            create_valid_response(),
        )
    )

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (
            first,
            second,
        ),
    )

    assert tuple(
        analysis.paper
        for analysis in result
    ) == (
        first,
        second,
    )
    assert len(provider.requests) == 2


def test_no_papers_returns_empty_without_provider_call() -> None:
    """Verify empty retained-paper input avoids provider execution."""

    provider = StubProvider(
        create_valid_response()
    )

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (),
    )

    assert result == ()
    assert provider.requests == []


def test_provider_instructions_limit_analysis_to_supplied_evidence() -> None:
    """Verify paper analysis remains grounded in supplied evidence."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response()
    )

    PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )

    instructions = provider.requests[0].system_instructions

    assert "bounded evidence sections" in instructions
    assert "Do not use outside knowledge." in instructions
    assert "Do not invent unsupported paper content." in instructions
    assert "Do not infer full-paper content" in instructions
    assert "Do not return or generate source identifiers" in instructions


def test_paper_analysis_uses_page_preserving_evidence() -> None:
    """Full-paper findings preserve supplied section and page provenance."""

    paper = create_paper()
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        authors=paper.authors,
        publication_year=paper.publication_year,
        abstract=paper.abstract,
        venue=paper.venue,
        source_url=paper.source_url,
        evidence_status=ResearchPaperEvidenceStatus.AVAILABLE,
        evidence_sections=(
            ResearchPaperEvidenceSection(
                section="Method",
                content="The model aligns video and text tokens.",
                page_number=4,
            ),
        ),
    )
    response = create_valid_response()
    for finding_name in ("problem", "approach"):
        response.structured_output[finding_name]["section"] = "Method"
        response.structured_output[finding_name]["page_number"] = 4
    for finding_name in (
        "representations",
        "modalities",
        "learning_objectives",
        "findings",
    ):
        for finding in response.structured_output[finding_name]:
            finding["section"] = "Method"
            finding["page_number"] = 4

    result = PaperAnalysisService(
        provider=StubProvider(response),
        model_name="qwen3:8b",
    ).analyze(create_request(), create_strategy(), (paper,))

    assert result[0].analysis_basis == ResearchPaperAnalysisBasis.PAPER_CONTENT
    assert result[0].approach.evidence[0].page_number == 4
    assert result[0].approach.evidence[0].section == "Method"


def test_paper_analysis_retains_abstract_with_full_paper_evidence() -> None:
    """Abstract-backed findings remain valid with full-paper evidence."""

    paper = create_paper()
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
        authors=paper.authors,
        publication_year=paper.publication_year,
        abstract=paper.abstract,
        venue=paper.venue,
        source_url=paper.source_url,
        evidence_status=ResearchPaperEvidenceStatus.AVAILABLE,
        evidence_sections=(
            ResearchPaperEvidenceSection(
                section="Method",
                content="The model aligns video and text tokens.",
                page_number=4,
            ),
        ),
    )

    provider = StubProvider(create_valid_response())

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(create_request(), create_strategy(), (paper,))

    payload = json.loads(provider.requests[0].user_prompt)

    assert result[0].approach.evidence[0].section == "Abstract"
    assert result[0].approach.evidence[0].page_number is None
    assert payload["paper"]["evidence_sections"][0]["section"] == "Abstract"
    assert payload["paper"]["evidence_sections"][1]["section"] == "Method"


def test_paper_analysis_skips_persistent_structural_failure() -> None:
    """A malformed paper response does not block a later paper."""

    invalid_paper = PaperMetadata(
        source_reference=create_paper().source_reference,
        title="Invalid Paper",
        evidence_status=ResearchPaperEvidenceStatus.AVAILABLE,
        evidence_sections=(
            ResearchPaperEvidenceSection(
                section="Method",
                content="The model aligns video and text tokens.",
                page_number=4,
            ),
        ),
    )
    valid_paper = create_paper(source_id="paper-002")
    provider = SequentialStubProvider(
        (
            create_valid_response(),
            create_valid_response(),
            create_valid_response(),
        )
    )

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (invalid_paper, valid_paper),
    )

    assert tuple(analysis.paper for analysis in result) == (valid_paper,)
    assert len(provider.requests) == 3


def test_paper_analysis_skips_discovery_only_paper() -> None:
    """A paper without usable evidence is not sent for analysis."""

    paper = create_paper()
    paper = PaperMetadata(
        source_reference=paper.source_reference,
        title=paper.title,
    )
    provider = StubProvider(create_valid_response())

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(create_request(), create_strategy(), (paper,))

    assert result == ()
    assert provider.requests == []
