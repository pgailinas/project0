from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from project0.agents.research.research_direction_analysis_service import (
    ResearchDirectionAnalysisService,
)
from project0.models.research_models import (
    ExistingResearchContext,
    PaperAnalysis,
    PaperMetadata,
    ResearchEvidenceReference,
    ResearchEvidenceSourceType,
    ResearchFinding,
    ResearchRequest,
    ResearchSourceReference,
)


class StubProvider:
    def __init__(self, outputs):
        self._outputs = list(outputs)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        output = self._outputs.pop(0)
        return SimpleNamespace(structured_output=output)


def _paper(source_id: str, title: str) -> PaperMetadata:
    reference = ResearchSourceReference(
        source_name="test",
        source_id=source_id,
        title=title,
        source_url=f"https://example.test/{source_id}",
    )
    return PaperMetadata(
        source_reference=reference,
        title=title,
        abstract="Abstract",
    )


def _paper_finding(source_id: str, content: str, page: int) -> ResearchFinding:
    return ResearchFinding(
        content=content,
        evidence=(
            ResearchEvidenceReference(
                source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
                source_id=source_id,
                page_number=page,
            ),
        ),
    )


def _paper_analysis(source_id: str, title: str, page: int) -> PaperAnalysis:
    paper = _paper(source_id, title)
    return PaperAnalysis(
        paper=paper,
        problem=_paper_finding(source_id, f"{title} problem", page),
        approach=_paper_finding(source_id, f"{title} approach", page),
        findings=(
            _paper_finding(source_id, f"{title} finding", page),
        ),
        limitations=(
            _paper_finding(source_id, f"{title} limitation", page),
        ),
    )


def _context() -> ExistingResearchContext:
    reference = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        source_id="context-doc",
        section="Limitations",
    )
    return ExistingResearchContext(
        limitations=(
            ResearchFinding(
                content="Semantic alignment remains limited.",
                evidence=(reference,),
            ),
        ),
    )


def _valid_output(*, with_context: bool = True):
    return {
        "synthesis": {
            "themes": [
                {
                    "content": "The analyzed papers use related alignment approaches.",
                    "evidence_ids": [
                        "E2",
                        "E7",
                    ],
                }
            ],
            "comparisons": [],
            "shared_limitations": [],
            "unresolved_questions": [],
        },
        "candidate_directions": [
            {
                "direction": "Investigate improved semantic alignment.",
                "rationale": "Prior limitations and literature support this investigation.",
                "context_evidence_ids": (
                    ["E0"] if with_context else []
                ),
                "literature_evidence_ids": [
                    "E3"
                ],
                "speculative": False,
            }
        ],
    }


def _request() -> ResearchRequest:
    return ResearchRequest(
        question="What should I investigate next?",
        guidance="Prefer technically relevant work.",
        constraints=("Use supplied evidence",),
        focus_areas=("semantic alignment",),
    )


def test_analyze_returns_empty_result_without_papers_or_provider_call():
    provider = StubProvider([])
    service = ResearchDirectionAnalysisService(provider, "test-model")

    result = service.analyze(_request(), _context(), ())

    assert result.synthesis.themes == ()
    assert result.synthesis.comparisons == ()
    assert result.synthesis.shared_limitations == ()
    assert result.synthesis.unresolved_questions == ()
    assert result.candidate_directions == ()
    assert provider.requests == []


def test_analyze_creates_context_grounded_synthesis_and_direction():
    provider = StubProvider([_valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )
    context = _context()

    result = service.analyze(_request(), context, papers)

    theme = result.synthesis.themes[0]
    assert [reference.source_id for reference in theme.evidence] == [
        "Paper-A",
        "Paper-B",
    ]
    assert [reference.page_number for reference in theme.evidence] == [3, 7]

    direction = result.candidate_directions[0]
    assert direction.context_evidence == context.limitations[0].evidence
    assert (
        direction.literature_evidence
        == papers[0].findings[0].evidence
    )
    assert direction.speculative is False
    assert len(provider.requests) == 1


def test_analyze_allows_literature_grounded_direction_without_context():
    provider = StubProvider([_valid_output(with_context=False)])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), None, papers)

    direction = result.candidate_directions[0]
    assert direction.context_evidence == ()
    assert direction.literature_evidence
    assert direction.speculative is False


def test_analyze_retries_once_after_invalid_output_then_succeeds():
    invalid = _valid_output()
    invalid["candidate_directions"][0]["literature_evidence_ids"] = [
        "unknown-evidence-id"
    ]
    provider = StubProvider([invalid, _valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert result.candidate_directions
    assert len(provider.requests) == 2
    retry_payload = json.loads(provider.requests[1].user_prompt)
    assert retry_payload["validation_feedback"] == (
        "Provider field 'candidate_directions.literature_evidence_ids' "
        "referenced unknown evidence identifier: unknown-evidence-id"
    )


def test_analyze_skips_invalid_synthesis_finding_without_retry():
    invalid = _valid_output()
    invalid["synthesis"]["themes"][0]["evidence_ids"] = [
        "E2"
    ]
    provider = StubProvider([invalid])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert result.synthesis.themes == ()
    assert result.candidate_directions
    assert len(provider.requests) == 1


def test_analyze_deduplicates_candidate_evidence_ids_without_retry():
    output = _valid_output()
    output["candidate_directions"][0]["literature_evidence_ids"] = [
        "E3",
        "E3",
    ]
    provider = StubProvider([output])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    direction = result.candidate_directions[0]
    assert (
        direction.literature_evidence
        == papers[0].findings[0].evidence
    )
    assert len(provider.requests) == 1


def test_analyze_accepts_valid_empty_provider_result_without_retry():
    output = {
        "synthesis": {
            "themes": [],
            "comparisons": [],
            "shared_limitations": [],
            "unresolved_questions": [],
        },
        "candidate_directions": [],
    }
    provider = StubProvider([output])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert result.synthesis.themes == ()
    assert result.candidate_directions == ()
    assert len(provider.requests) == 1


def test_analyze_allows_evidence_anchored_speculative_direction():
    output = _valid_output()
    output["candidate_directions"] = [
        {
            "direction": "Explore a broader alignment target.",
            "rationale": "This extrapolates from the supplied alignment evidence.",
            "context_evidence_ids": [],
            "literature_evidence_ids": ["E2"],
            "speculative": True,
        }
    ]
    provider = StubProvider([output])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert result.candidate_directions[0].speculative is True
    assert result.candidate_directions[0].literature_evidence


def test_provider_request_uses_structured_findings_and_prohibits_novelty_claims():
    provider = StubProvider([_valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    service.analyze(_request(), _context(), papers)

    request = provider.requests[0]
    payload = json.loads(request.user_prompt)

    assert payload["research_request"]["question"] == _request().question
    assert payload["existing_research_context"]["limitations"][0][
        "finding_id"
    ] == "E0"
    assert payload["paper_analyses"][0]["problem"]["finding_id"] == "E1"
    assert "page_number" not in request.user_prompt
    assert payload["allowed_evidence_ids"]["context_evidence_ids"] == [
        "E0"
    ]
    assert payload["allowed_evidence_ids"]["literature_evidence_ids"] == [
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        "E6",
        "E7",
        "E8",
    ]
    assert payload["validation_feedback"] is None

    direction_schema = request.response_schema["properties"][
        "candidate_directions"
    ]["items"]["properties"]
    assert direction_schema["context_evidence_ids"] == {
        "type": "array"
    }
    assert direction_schema["literature_evidence_ids"] == {
        "type": "array"
    }

    instructions = request.system_instructions.lower()
    assert "do not use outside knowledge" in instructions
    assert "do not claim novelty" in instructions
    assert "broader literature" in instructions
