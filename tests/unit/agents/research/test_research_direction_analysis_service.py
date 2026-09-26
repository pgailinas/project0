# ============================================================
# Project0 - Research Direction Analysis Service Tests
#
# File: test_research_direction_analysis_service.py
#
# Purpose:
#     Verify research direction analysis orchestration, evidence
#     provenance validation, and bounded analysis input behavior.
#
# ============================================================

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
                        "literature-002",
                        "literature-007",
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
                    ["context-001"] if with_context else []
                ),
                "literature_evidence_ids": [
                    "literature-003"
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

    context_evidence_schema = provider.requests[0].response_schema[
        "properties"
    ]["candidate_directions"]["items"]["properties"][
        "context_evidence_ids"
    ]
    assert context_evidence_schema == {
        "type": "array",
        "items": {"type": "string"},
        "uniqueItems": True,
        "maxItems": 0,
    }


def test_retry_skips_adjacent_direction_and_preserves_valid_results(caplog):
    """A bad retried direction does not erase valid synthesis or directions."""

    invalid = _valid_output(with_context=False)
    invalid["candidate_directions"][0]["literature_evidence_ids"] = [
        "literature-007"
    ]
    retry = _valid_output(with_context=False)
    retry["candidate_directions"].insert(
        0,
        {
            "direction": "Misclassified adjacent direction.",
            "rationale": "Adjacent literature would require adaptation.",
            "context_evidence_ids": [],
            "literature_evidence_ids": ["literature-007"],
            "speculative": False,
        },
    )
    provider = StubProvider([invalid, retry])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    with caplog.at_level("WARNING"):
        result = service.analyze(
            _request(),
            None,
            papers,
            direction_eligible_source_ids=frozenset({"Paper-A"}),
        )

    assert result.synthesis.themes
    assert [
        direction.direction
        for direction in result.candidate_directions
    ] == ["Investigate improved semantic alignment."]
    assert result.warnings == (
        "1 invalid candidate research direction was omitted after "
        "corrective validation.",
    )
    assert len(provider.requests) == 2
    assert (
        "Skipping invalid candidate research direction after the corrective "
        "retry: Non-speculative candidate direction cites literature that "
        "was not classified as direct or transferable."
        in caplog.text
    )

    payload = json.loads(provider.requests[0].user_prompt)
    assert payload["allowed_evidence_ids"][
        "non_speculative_direction_literature_evidence_ids"
    ] == [
        "literature-001",
        "literature-002",
        "literature-003",
        "literature-004",
    ]


def test_speculative_direction_allows_adjacent_literature_anchor():
    """Adjacent evidence remains available for labeled extrapolation."""

    output = _valid_output(with_context=False)
    direction = output["candidate_directions"][0]
    direction["literature_evidence_ids"] = ["literature-007"]
    direction["speculative"] = True
    provider = StubProvider([output])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(
        _request(),
        None,
        papers,
        direction_eligible_source_ids=frozenset({"Paper-A"}),
    )

    assert result.candidate_directions[0].speculative is True
    assert result.candidate_directions[0].literature_evidence[
        0
    ].source_id == "Paper-B"


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
        "literature-002"
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


def test_analyze_retries_when_candidate_evidence_ids_are_duplicated():
    invalid = _valid_output()
    invalid["candidate_directions"][0]["literature_evidence_ids"] = [
        "literature-003",
        "literature-003",
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
        "must not contain duplicates."
    )


def test_analyze_retries_when_candidate_bulk_cites_literature_evidence():
    invalid = _valid_output()
    invalid["candidate_directions"][0]["literature_evidence_ids"] = [
        "literature-001",
        "literature-002",
        "literature-003",
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
        "must contain no more than 2 evidence identifiers."
    )


def test_analyze_retries_when_candidate_evidence_uses_wrong_source_type():
    invalid = _valid_output()
    invalid["candidate_directions"][0]["context_evidence_ids"] = [
        "literature-003"
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
        "Provider field 'candidate_directions.context_evidence_ids' "
        "referenced evidence from the wrong source type."
    )


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
            "literature_evidence_ids": ["literature-002"],
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


def test_analyze_retries_when_comparison_reverses_unsupported_performance_order():
    invalid = _valid_output()
    invalid["synthesis"]["comparisons"] = [
        {
            "content": (
                "Self-supervised autoencoders perform better than direct "
                "multimodal inference using CLIP."
            ),
            "evidence_ids": [
                "literature-002",
                "literature-007",
            ],
        }
    ]
    provider = StubProvider([invalid, _valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert result.synthesis.comparisons == ()
    assert len(provider.requests) == 2
    retry_payload = json.loads(provider.requests[1].user_prompt)
    assert retry_payload["validation_feedback"] == (
        "Provider field 'comparisons.content' makes an explicit "
        "performance-ordering claim that is not directly stated by "
        "the cited literature evidence."
    )


def test_analyze_skips_unsupported_comparison_after_corrective_retry():
    invalid = _valid_output()
    invalid["synthesis"]["comparisons"] = [
        {
            "content": (
                "Self-supervised autoencoders perform better than direct "
                "multimodal inference using CLIP."
            ),
            "evidence_ids": [
                "literature-002",
                "literature-007",
            ],
        }
    ]
    retry = json.loads(json.dumps(invalid))
    provider = StubProvider([invalid, retry])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    )

    result = service.analyze(_request(), _context(), papers)

    assert len(provider.requests) == 2
    assert result.synthesis.comparisons == ()
    assert result.synthesis.themes
    assert result.candidate_directions


def test_analyze_accepts_explicit_performance_order_supported_by_literature():
    first = _paper_analysis("Paper-A", "Paper A", 3)
    first = PaperAnalysis(
        paper=first.paper,
        problem=first.problem,
        approach=first.approach,
        findings=(
            _paper_finding(
                "Paper-A",
                "Paper A outperforms the comparison baseline.",
                3,
            ),
        ),
        limitations=first.limitations,
    )
    second = _paper_analysis("Paper-B", "Paper B", 7)
    output = _valid_output()
    output["synthesis"]["comparisons"] = [
        {
            "content": "Paper A outperforms the comparison baseline.",
            "evidence_ids": [
                "literature-003",
                "literature-007",
            ],
        }
    ]
    provider = StubProvider([output])
    service = ResearchDirectionAnalysisService(provider, "test-model")

    result = service.analyze(
        _request(),
        _context(),
        (first, second),
    )

    assert result.synthesis.comparisons
    assert len(provider.requests) == 1


def test_provider_request_limits_direction_analysis_to_five_papers():
    provider = StubProvider([_valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    papers = tuple(
        _paper_analysis(
            f"Paper-{index}",
            f"Paper {index}",
            index,
        )
        for index in range(1, 7)
    )

    service.analyze(_request(), _context(), papers)

    request = provider.requests[0]
    payload = json.loads(request.user_prompt)

    assert request.metadata["paper_analysis_count"] == 5
    assert request.metadata["timeout_seconds"] == 600.0
    assert [
        paper["source_id"]
        for paper in payload["paper_analyses"]
    ] == [
        "Paper-1",
        "Paper-2",
        "Paper-3",
        "Paper-4",
        "Paper-5",
    ]


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
    ] == "context-001"
    assert (
        payload["paper_analyses"][0]["problem"]["finding_id"]
        == "literature-001"
    )
    assert "page_number" not in request.user_prompt
    assert payload["allowed_evidence_ids"]["context_evidence_ids"] == [
        "context-001"
    ]
    assert payload["allowed_evidence_ids"]["literature_evidence_ids"] == [
        "literature-001",
        "literature-002",
        "literature-003",
        "literature-004",
        "literature-005",
        "literature-006",
        "literature-007",
        "literature-008",
    ]
    assert payload["validation_feedback"] is None

    direction_schema = request.response_schema["properties"][
        "candidate_directions"
    ]["items"]["properties"]
    assert direction_schema["context_evidence_ids"] == {
        "type": "array",
        "items": {
            "type": "string",
            "enum": ["context-001"],
        },
        "uniqueItems": True,
    }
    assert direction_schema["literature_evidence_ids"] == {
        "type": "array",
        "items": {
            "type": "string",
            "enum": [
                "literature-001",
                "literature-002",
                "literature-003",
                "literature-004",
                "literature-005",
                "literature-006",
                "literature-007",
                "literature-008",
            ],
        },
        "uniqueItems": True,
        "maxItems": 2,
    }

    synthesis_schema = request.response_schema["properties"][
        "synthesis"
    ]["properties"]["themes"]["items"]["properties"]["evidence_ids"]
    assert synthesis_schema["uniqueItems"] is True
    assert synthesis_schema["maxItems"] == 2

    instructions = request.system_instructions.lower()
    assert "do not use outside knowledge" in instructions
    assert "directly support the specific claim content" in instructions
    assert "performance ordering claims" in instructions
    assert "do not infer, reverse, or import such comparisons" in instructions
    assert "smallest sufficient evidence set" in instructions
    assert "synthesis fields are literature-only" in instructions
    assert "do not claim novelty" in instructions
    assert "broader literature" in instructions


def test_direction_prompt_adapts_to_request_without_invention():
    provider = StubProvider([_valid_output(), _valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    request = ResearchRequest(
        question="How can video autoencoders learn temporal representations?",
        guidance="Compare methods against existing baselines.",
        constraints=("Limited GPU resources",),
    )
    service.analyze(request, _context(), (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    ))
    payload = json.loads(provider.requests[0].user_prompt)
    instructions = provider.requests[0].system_instructions.lower()
    assert payload["research_request"]["constraints"] == ["Limited GPU resources"]
    assert "do not impose experimental design" in instructions
    assert "when a controlled comparison" in instructions
    assert "when feasibility" in instructions
    assert "do not invent datasets" in instructions


def test_conceptual_request_does_not_require_experiment():
    provider = StubProvider([_valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    service.analyze(ResearchRequest(
        question="Which theoretical interpretations emerge?",
        guidance="Provide a conceptual literature review.",
    ), _context(), (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    ))
    assert len(provider.requests) == 1


def test_requirements_in_constraints_trigger_targeted_retry():
    provider = StubProvider([_valid_output(), _valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    service.analyze(ResearchRequest(
        question="What should be investigated?",
        constraints=("Include ablations, evaluation and compute budget",),
    ), _context(), (
        _paper_analysis("Paper-A", "Paper A", 3),
        _paper_analysis("Paper-B", "Paper B", 7),
    ))
    assert len(provider.requests) == 2
    feedback = json.loads(provider.requests[1].user_prompt)["validation_feedback"]
    assert "controlled comparison or ablation" in feedback
    assert "evaluation or unresolved" in feedback
    assert "resource dependency" in feedback


def test_compute_constrained_ablation_request_retries_generic_directions():
    generic = _valid_output()
    corrected = _valid_output()
    corrected["candidate_directions"][0]["direction"] = (
        "Adapt the documented encoder objective for the existing baseline."
    )
    corrected["candidate_directions"][0]["rationale"] = (
        "Keep the existing baseline fixed; compare against a controlled "
        "ablation, evaluate downstream accuracy, and check GPU feasibility "
        "before any full training."
    )
    provider = StubProvider([generic, corrected])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    request = ResearchRequest(
        question="Which experiment should be run?",
        guidance="Include ablation studies feasible with limited GPU resources.",
    )

    result = service.analyze(
        request,
        _context(),
        (
            _paper_analysis("Paper-A", "Paper A", 3),
            _paper_analysis("Paper-B", "Paper B", 7),
        ),
    )

    assert len(provider.requests) == 2
    assert "controlled comparison or ablation" in json.loads(
        provider.requests[1].user_prompt
    )["validation_feedback"]
    assert "GPU feasibility" in result.candidate_directions[0].rationale


def test_compute_constrained_ablation_retry_preserves_evidence_valid_result(caplog):
    provider = StubProvider([_valid_output(), _valid_output()])
    service = ResearchDirectionAnalysisService(provider, "test-model")
    request = ResearchRequest(
        question="Which experiment should be run?",
        guidance="Include ablations feasible with limited Colab compute.",
    )

    result = service.analyze(
        request,
        _context(),
        (
            _paper_analysis("Paper-A", "Paper A", 3),
            _paper_analysis("Paper-B", "Paper B", 7),
        ),
    )

    assert len(provider.requests) == 2
    assert len(result.candidate_directions) == 1
    assert "synthesis remains incomplete" in caplog.text
