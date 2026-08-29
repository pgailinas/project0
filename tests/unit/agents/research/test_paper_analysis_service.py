# ============================================================
# Project0 - Paper Analysis Service Tests
#
# File: test_paper_analysis_service.py
#
# Purpose:
#     Verify retained-paper reasoning orchestration,
#     full-text fallback, provenance, and failure behavior.
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
    ResearchPaperDocument,
    ResearchPaperDocumentType,
    ResearchPaperExtractionStatus,
    ResearchPaperPage,
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


def create_document(
    paper: PaperMetadata | None = None,
) -> ResearchPaperDocument:
    """Create a page-preserving retained paper document."""

    return ResearchPaperDocument(
        paper=paper or create_paper(),
        source_url="https://example.test/paper.pdf",
        document_type=ResearchPaperDocumentType.PDF,
        extraction_method="pypdf",
        pages=(
            ResearchPaperPage(
                page_number=1,
                text="The paper studies semantic video alignment.",
            ),
            ResearchPaperPage(
                page_number=2,
                text=(
                    "A contrastive objective aligns video and "
                    "language embeddings."
                ),
            ),
            ResearchPaperPage(
                page_number=3,
                text="Experiments evaluate representation quality.",
            ),
        ),
        extraction_status=ResearchPaperExtractionStatus.COMPLETED,
        document_id="document-001",
    )


def create_valid_response(
    source_id: str = "paper-001",
    *,
    page_numbers: list[int] | None = None,
) -> ProviderResponse:
    """Create a valid structured paper analysis response."""

    pages = (
        page_numbers
        if page_numbers is not None
        else [1]
    )

    def finding(
        content: str,
        page_numbers_value: list[int] | None = None,
    ) -> dict:
        return {
            "content": content,
            "page_numbers": (
                pages
                if page_numbers_value is None
                else page_numbers_value
            ),
            "section": None,
        }

    return ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output={
            "source_id": source_id,
            "problem": finding(
                "The paper studies semantic alignment."
            ),
            "approach": finding(
                "The paper uses contrastive representation learning.",
                [2] if pages else [],
            ),
            "representations": [
                finding(
                    "Video and language embeddings are aligned.",
                    [2] if pages else [],
                ),
            ],
            "modalities": [
                finding(
                    "The method uses video and text.",
                ),
            ],
            "learning_objectives": [
                finding(
                    "A contrastive objective provides alignment.",
                    [2] if pages else [],
                ),
            ],
            "datasets_tasks": [],
            "findings": [
                finding(
                    "The representation supports semantic comparison.",
                    [3] if pages else [],
                ),
            ],
            "limitations": [],
            "research_relevance": finding(
                "The method directly informs video-language alignment."
            ),
            "warnings": [],
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
    )


def test_full_text_analysis_creates_structured_analysis() -> None:
    """Verify full-text paper analysis creation."""

    paper = create_paper()
    document = create_document(paper)
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
        (document,),
    )

    assert len(result) == 1

    analysis = result[0]

    assert analysis.paper is paper
    assert (
        analysis.analysis_basis
        == ResearchPaperAnalysisBasis.FULL_TEXT
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
    assert analysis.research_relevance is not None
    assert analysis.warnings == ()


def test_full_text_analysis_constructs_page_provenance() -> None:
    """Verify full-text findings receive page-level provenance."""

    paper = create_paper()
    document = create_document(paper)

    analysis = PaperAnalysisService(
        provider=StubProvider(
            create_valid_response()
        ),
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
        (document,),
    )[0]

    evidence = analysis.approach.evidence[0]

    assert (
        evidence.source_type
        == ResearchEvidenceSourceType.RESEARCH_PAPER
    )
    assert evidence.source_id == "paper-001"
    assert evidence.page_number == 2
    assert evidence.section is None


def test_full_text_request_includes_page_preserving_text() -> None:
    """Verify full-text page numbers and text are sent to the provider."""

    paper = create_paper()
    document = create_document(paper)
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
        (document,),
    )

    payload = json.loads(
        provider.requests[0].user_prompt
    )

    assert payload["paper"]["source_id"] == "paper-001"
    assert payload["paper"]["analysis_basis"] == "full_text"
    assert payload["paper"]["document_id"] == "document-001"
    assert payload["paper"]["pages"] == [
        {
            "page_number": 1,
            "text": "The paper studies semantic video alignment.",
        },
        {
            "page_number": 2,
            "text": (
                "A contrastive objective aligns video and "
                "language embeddings."
            ),
        },
        {
            "page_number": 3,
            "text": "Experiments evaluate representation quality.",
        },
    ]


def test_metadata_fallback_is_explicit() -> None:
    """Verify absent full text produces metadata/abstract analysis."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response(
            page_numbers=[],
        )
    )

    analysis = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
    )[0]

    assert (
        analysis.analysis_basis
        == ResearchPaperAnalysisBasis.ABSTRACT_METADATA
    )
    assert analysis.warnings[0] == (
        "Full text was unavailable; analysis is limited to "
        "paper metadata and abstract."
    )
    assert analysis.problem.evidence[0].page_number is None
    assert analysis.problem.evidence[0].source_id == "paper-001"


def test_metadata_fallback_request_excludes_full_text_pages() -> None:
    """Verify metadata fallback supplies abstract instead of pages."""

    paper = create_paper()
    provider = StubProvider(
        create_valid_response(
            page_numbers=[],
        )
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

    assert payload["paper"]["analysis_basis"] == "abstract_metadata"
    assert payload["paper"]["abstract"] == paper.abstract
    assert "pages" not in payload["paper"]
    assert "document_id" not in payload["paper"]


def test_metadata_fallback_rejects_invented_page_provenance() -> None:
    """Verify metadata-only analysis cannot invent page numbers."""

    response = create_valid_response()

    provider = SequentialStubProvider(
        (
            response,
            response,
        )
    )

    with pytest.raises(
        ValueError,
        match="invented page provenance",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (create_paper(),),
        )

    assert len(provider.requests) == 2


def test_full_text_analysis_rejects_unknown_page_number() -> None:
    """Verify full-text evidence must cite an existing paper page."""

    response = create_valid_response(
        page_numbers=[99],
    )

    provider = SequentialStubProvider(
        (
            response,
            response,
        )
    )

    paper = create_paper()

    with pytest.raises(
        ValueError,
        match="unknown paper page numbers",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (paper,),
            (create_document(paper),),
        )

    assert len(provider.requests) == 2


def test_full_text_analysis_requires_page_provenance() -> None:
    """Verify full-text findings must cite at least one page."""

    response = create_valid_response(
        page_numbers=[],
    )

    provider = SequentialStubProvider(
        (
            response,
            response,
        )
    )

    paper = create_paper()

    with pytest.raises(
        ValueError,
        match="must cite at least one page",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (paper,),
            (create_document(paper),),
        )

    assert len(provider.requests) == 2


def test_unknown_source_id_retries_once() -> None:
    """Verify unknown paper source identifiers trigger one retry."""

    provider = SequentialStubProvider(
        (
            create_valid_response(
                source_id="paper-999",
            ),
            create_valid_response(),
        )
    )

    paper = create_paper()

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
        (create_document(paper),),
    )

    assert len(result) == 1
    assert len(provider.requests) == 2


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

    paper = create_paper()

    result = PaperAnalysisService(
        provider=provider,
        model_name="qwen3:8b",
    ).analyze(
        create_request(),
        create_strategy(),
        (paper,),
        (create_document(paper),),
    )

    assert len(result) == 1
    assert len(provider.requests) == 2


def test_provider_error_propagates_without_retry() -> None:
    """Verify provider failures propagate to workflow handling."""

    provider = StubProvider(
        create_valid_response(),
        error=RuntimeError("Provider unavailable."),
    )

    paper = create_paper()

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
            (paper,),
            (create_document(paper),),
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
            create_valid_response(
                source_id="paper-001",
            ),
            create_valid_response(
                source_id="paper-002",
            ),
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
        (
            create_document(first),
            ResearchPaperDocument(
                paper=second,
                source_url="https://example.test/second.pdf",
                document_type=ResearchPaperDocumentType.PDF,
                extraction_method="pypdf",
                pages=create_document(second).pages,
                extraction_status=ResearchPaperExtractionStatus.COMPLETED,
                document_id="document-002",
            ),
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


def test_unknown_document_source_id_is_rejected_before_provider() -> None:
    """Verify documents must belong to retained papers."""

    retained_paper = create_paper(
        source_id="paper-001",
    )
    unknown_paper = create_paper(
        source_id="paper-999",
    )
    provider = StubProvider(
        create_valid_response()
    )

    with pytest.raises(
        ValueError,
        match="document for an unknown source identifier",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (retained_paper,),
            (create_document(unknown_paper),),
        )

    assert provider.requests == []


def test_duplicate_documents_are_rejected_before_provider() -> None:
    """Verify at most one full-text document is accepted per paper."""

    paper = create_paper()
    first_document = create_document(paper)
    second_document = ResearchPaperDocument(
        paper=paper,
        source_url="https://example.test/second.pdf",
        document_type=ResearchPaperDocumentType.PDF,
        extraction_method="pypdf",
        pages=first_document.pages,
        extraction_status=ResearchPaperExtractionStatus.COMPLETED,
        document_id="document-002",
    )
    provider = StubProvider(
        create_valid_response()
    )

    with pytest.raises(
        ValueError,
        match="duplicate documents",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (paper,),
            (
                first_document,
                second_document,
            ),
        )

    assert provider.requests == []


def test_document_metadata_must_match_retained_paper() -> None:
    """Verify document metadata cannot replace retained paper metadata."""

    retained_paper = create_paper()
    different_metadata = PaperMetadata(
        source_reference=retained_paper.source_reference,
        title="Different Title",
        abstract=retained_paper.abstract,
    )

    provider = StubProvider(
        create_valid_response()
    )

    with pytest.raises(
        ValueError,
        match="document metadata did not match",
    ):
        PaperAnalysisService(
            provider=provider,
            model_name="qwen3:8b",
        ).analyze(
            create_request(),
            create_strategy(),
            (retained_paper,),
            (create_document(different_metadata),),
        )

    assert provider.requests == []


def test_provider_instructions_prohibit_outside_knowledge() -> None:
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
        (create_document(paper),),
    )

    instructions = provider.requests[0].system_instructions

    assert "Do not use outside knowledge." in instructions
    assert "Do not invent unsupported paper content." in instructions
    assert (
        "Every substantive finding must cite one or more supplied "
        "page numbers"
        in instructions
    )
    assert (
        "source_id is an opaque identifier and must be returned "
        "exactly as supplied"
        in instructions
    )
