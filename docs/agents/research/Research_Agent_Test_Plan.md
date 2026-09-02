# Research Agent Test Plan

**Version:** 0.3  
**Owner:** Project0  
**Last Updated:** 2026-09-02

------------------------------------------------------------------------

## Executive Summary

This document defines the verification criteria and test strategy for
the Project0 Research Agent across unit, integration, browser
acceptance, and exploratory AI testing.

The purpose of this test plan is to demonstrate that the Research Agent
can accept research questions, develop research strategies, discover
relevant technical papers through supported external research sources,
retrieve paper metadata, evaluate paper relevance, optionally process
Existing Research Context, perform structured per-paper and research
direction analysis, generate evidence-grounded research artifacts,
preserve citation and source information, and present useful research
results while preserving human research authority.

The Research Agent is the second reference implementation of a Project0
AI Agent. Successful completion of this test plan provides additional
validation that the Project0 layered testing approach can support
multiple specialized agents.

------------------------------------------------------------------------

## 1. Purpose

The Research Agent Test Plan establishes the required verification
activities before the Research Agent can be considered complete.

This document defines:

-   verification objectives
-   functional verification scenarios
-   research integrity requirements
-   AI reasoning verification
-   source and citation verification
-   browser acceptance requirements
-   completion criteria

Detailed test execution procedures may be defined in a **Research Agent
Testing Guide**.

Verification scenario identifiers such as `RA-FUN-001`, `RA-SRC-001`,
and `RA-AI-001` identify the behavior being verified and are independent
of the testing layer used to provide evidence.

Automated test names add a testing-layer prefix when a scenario is
implemented at a specific layer:

-   `INT` --- integration verification through assembled Project0
    Python/service boundaries
-   `UI` --- browser acceptance verification through the Dashboard/UI
    boundary

For example, `RA-FUN-001` may be verified by both `INT-RA-FUN-001` and
`UI-RA-FUN-001` without creating separate requirement identifiers.

------------------------------------------------------------------------

## 2. Test Objectives

The Research Agent shall demonstrate the ability to:

-   Process research requests through the Project0 workflow.
-   Generate an appropriate structured research strategy.
-   Generate deterministic research search terms from the research
    strategy.
-   Search supported external research sources.
-   Retrieve and normalize available paper metadata.
-   Identify and rank papers relevant to the research question.
-   Verify bounded semantic relevance scoring and normalization.
-   Verify configured maximum-result selection while preserving all
    discovered source references.
-   Verify bounded batch processing for research evaluation.
-   Verify bounded retry behavior for invalid or incomplete research
    evaluation responses within a batch.
-   Preserve citation and source information.
-   Verify optional Existing Research Context document ingestion and
    analysis.
-   Verify structured per-paper analysis.
-   Verify cross-paper synthesis and Research Direction Analysis.
-   Verify page- or section-level provenance for context-derived
    information.
-   Verify existing workflow semantics when no context document is
    provided.
-   Generate evidence-grounded research artifacts.
-   Compare research methods and approaches.
-   Identify potential research gaps.
-   Generate useful experiment planning suggestions.
-   Support human review of research results.
-   Operate within Project0 platform boundaries.

------------------------------------------------------------------------

## 3. Test Scope

### 3.1 In Scope

This test plan covers:

-   Research request processing
-   Research strategy generation
-   Deterministic research query generation
-   External research source integration
-   Paper metadata retrieval
-   Candidate paper identification
-   Paper relevance evaluation
-   Research relevance score normalization
-   Maximum-result ranking and selection
-   Research evaluation batch processing
-   Research evaluation retry handling
-   Optional Existing Research Context document ingestion
-   Existing Research Context analysis
-   Bounded context document chunking
-   Context provenance tracking
-   Per-paper analysis
-   Cross-paper synthesis
-   Research Direction Analysis
-   Research analysis validation
-   Citation and source tracking
-   Paper summary generation
-   Literature comparison
-   Research gap identification
-   Experiment planning support
-   Research artifact validation
-   Research Agent dashboard interaction
-   Local reasoning provider integration
-   Research source provider abstraction and deterministic provider
    validation
-   Multiple external research source provider integration
-   Research Agent platform integration

------------------------------------------------------------------------

### 3.2 Out of Scope

This test plan does not evaluate:

-   General AI model capability
-   AI model benchmarking
-   Scientific correctness of published research
-   Exhaustive literature coverage
-   Semantic research retrieval
-   Vector-based knowledge search
-   Multi-agent research workflows
-   Autonomous experiment execution
-   OCR processing for image-only or scanned PDF context documents

------------------------------------------------------------------------

## 4. Verification Principles

### Evidence Grounding

Research Agent outputs shall be based on identifiable research sources.

AI-generated analysis shall remain distinguishable from source
information.

Source-derived context findings, source-derived per-paper
interpretation, and Research Agent inference shall remain
distinguishable.

------------------------------------------------------------------------

### Human Authority

The Research Agent shall preserve human decision authority.

The agent may identify research opportunities and suggest experiments
but shall not independently establish scientific validity or research
conclusions.

------------------------------------------------------------------------

### Source Traceability

Research findings and generated artifacts shall preserve available
citation and source information.

Missing source or metadata information shall not be invented.

------------------------------------------------------------------------

### Deterministic Before AI

External source access, metadata normalization, validation, workflow
coordination, and artifact handling shall use deterministic processing
whenever AI reasoning is not required.

------------------------------------------------------------------------

### Safe Research Evaluation

The Research Agent shall report uncertainty or insufficient evidence
when:

-   source information is incomplete
-   metadata cannot be retrieved
-   relevance cannot be established reliably
-   generated analysis is unsupported by available evidence

------------------------------------------------------------------------

### Platform Separation

Research Agent functionality shall remain separate from reusable
Project0 platform infrastructure.

Agent-specific responsibilities shall not be embedded into shared
platform components.

------------------------------------------------------------------------

## 5. Functional Verification Scenarios

------------------------------------------------------------------------

### 5.1 RA-FUN-001: Research Request Processing

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that a user can submit a research request through the Research
Agent interface.

#### Expected Behavior

The system shall:

-   accept the request
-   process the workflow
-   generate a structured research result

#### Pass Criteria

A valid research request completes successfully and produces reviewable
research output.

------------------------------------------------------------------------

### 5.2 RA-FUN-002: Research Strategy Generation

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent transforms a research question into an
appropriate research strategy.

#### Test Scenario

Submit a research question containing a defined technical research
topic.

#### Expected Behavior

The Research Agent shall:

-   identify the research objective
-   identify relevant research concepts
-   identify explicit research sub-questions when present
-   preserve optional constraints and focus areas
-   generate deterministic provider-ready research search terms

#### Pass Criteria

The generated Research Strategy is consistent with the submitted
research question and contains sufficient information for research
source discovery.

------------------------------------------------------------------------

### 5.3 RA-FUN-003: Candidate Paper Identification

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent identifies candidate papers relevant to
the research strategy.

#### Expected Behavior

The Research Agent shall:

-   search supported research sources
-   return candidate research papers
-   preserve source identifiers
-   avoid introducing unsupported candidate references

#### Pass Criteria

Candidate papers originate from supported research sources and retain
identifiable source information.

------------------------------------------------------------------------

### 5.4 RA-FUN-004: Paper Relevance Evaluation

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that candidate papers are evaluated against the research
question.

#### Expected Behavior

The Research Agent shall:

-   evaluate candidate papers in bounded batches
-   combine validated batch results
-   evaluate paper relevance using the defined bounded relevance scale
-   normalize valid provider relevance scores for downstream use
-   distinguish direct research-question alignment from partial,
    adjacent, or topical relevance
-   rank candidate papers by relevance
-   retain the configured maximum number of highest-relevance papers
-   preserve all discovered source references for traceability
-   provide relevance explanations
-   preserve references to supporting paper information

#### Pass Criteria

Research evaluations are traceable to candidate papers, use consistent
semantic relevance criteria, preserve relevance ordering after score
normalization, and retain the configured maximum number of results
without discarding discovered source references.

------------------------------------------------------------------------

### 5.5 RA-FUN-005: Paper Summary Generation

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent presents a structured result for each
retained paper.

#### Expected Behavior

The Research Agent shall:

-   present paper metadata and relevance assessment
-   present structured analysis only when abstract-supported analysis is
    available
-   distinguish paper content from relevance strengths and limitations
-   preserve source traceability without repeated visible source URLs

#### Pass Criteria

Each retained-paper result is consolidated, traceable to the source
paper, and contains no unsupported source claims.

------------------------------------------------------------------------

### 5.6 RA-FUN-006: Literature Comparison

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent can compare multiple relevant research
papers.

#### Expected Behavior

The Research Agent shall:

-   compare research methods
-   identify similarities and differences
-   preserve references to compared papers
-   distinguish source facts from generated comparison analysis

#### Pass Criteria

The comparison accurately associates analyzed methods and observations
with the appropriate research sources.

------------------------------------------------------------------------

### 5.7 RA-FUN-007: Research Gap Identification

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent can identify potential research gaps from
reviewed literature.

#### Expected Behavior

The Research Agent shall:

-   identify limitations supported by reviewed sources
-   distinguish observed limitations from generated research
    opportunities
-   preserve supporting source references
-   avoid presenting generated opportunities as established facts

#### Pass Criteria

Potential research gaps are supported by reviewed literature and clearly
identified as Research Agent analysis.

------------------------------------------------------------------------

### 5.8 RA-FUN-008: Experiment Planning Support

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent can generate experiment planning
suggestions based on research findings.

#### Expected Behavior

The Research Agent shall:

-   relate experiment suggestions to the research question
-   identify supporting research evidence
-   preserve source references
-   distinguish suggested experiments from published methods and results

#### Pass Criteria

Experiment suggestions are traceable to research findings and are
presented as recommendations rather than established conclusions.

------------------------------------------------------------------------

### 5.9 RA-FUN-009: Research Request Revision Workflow

#### Verification Layers

-   Unit
-   UI Acceptance where applicable

#### Objective

Verify that a user can revise a research request or generated research
output while preserving the original research context.

#### Test Scenario

Submit a research request, generate a reviewable result, revise the
request or research focus, and resubmit.

#### Expected Behavior

The Research Agent shall:

-   preserve the original research request
-   preserve optional research constraints
-   allow the user to update or append revision instructions
-   process the revised request through the normal research workflow
-   preserve applicable source and citation information

#### Pass Criteria

The revised request completes a new research cycle and produces a
reviewable Research Result without losing applicable research context.

------------------------------------------------------------------------

### 5.10 RA-FUN-010: Existing Research Context Processing

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify optional Existing Research Context document ingestion and
analysis.

#### Expected Behavior

The Research Agent shall:

-   accept text-based PDF, Markdown, and plain-text context documents
-   avoid storing a copy of the selected source document
-   preserve page- or section-level provenance
-   use bounded chunking for large documents with implementation limits
    to be defined
-   produce structured Existing Research Context containing the research
    problem, prior work, implemented approaches, findings, limitations,
    unresolved questions, stated future work, and source references
-   clearly report extraction or analysis failures
-   reject image-only or scanned PDF documents requiring OCR

#### Pass Criteria

Supported context documents produce structured, source-traceable
Existing Research Context, and unsupported or failed context processing
does not silently revert to the no-context workflow.

------------------------------------------------------------------------

### 5.11 RA-FUN-011: Per-Paper Analysis

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify structured technical analysis for retained papers.

#### Expected Behavior

The Research Agent shall produce Paper Analysis containing:

-   problem
-   approach
-   representations
-   modalities
-   learning or alignment objective
-   datasets or tasks
-   findings
-   limitations
-   relevance to the current research
-   evidence references

#### Pass Criteria

Each Paper Analysis is traceable to a retained paper, preserves evidence
references, and does not invent missing source information.

------------------------------------------------------------------------

### 5.12 RA-FUN-012: Research Direction Analysis

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify cross-paper synthesis and evidence-grounded candidate research
direction generation.

#### Expected Behavior

The Research Agent shall:

-   produce synthesis findings containing themes, comparisons, shared
    limitations, and unresolved questions
-   identify candidate research directions
-   preserve context motivation and literature evidence for candidate
    directions unless explicitly marked speculative
-   preserve provenance for referenced context items and papers
-   distinguish Research Agent inference from source-derived findings
    and per-paper interpretation

#### Pass Criteria

Research Direction Analysis remains traceable to valid context and paper
evidence and satisfies the defined synthesis requirements.

Unknown context items or paper identifiers are rejected, and each
non-speculative candidate direction preserves context motivation and
literature evidence.

------------------------------------------------------------------------

### 5.13 RA-FUN-013: No-Context Backward Compatibility

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the optional Existing Research Context capability does not
change existing Research Agent behavior when no context document is
provided.

#### Expected Behavior

The Research Agent shall preserve existing workflow semantics and result
behavior with new optional context fields empty.

#### Pass Criteria

A request with `context_document=None` follows the existing workflow and
produces the expected Research Result without requiring context
processing.

------------------------------------------------------------------------

## 6. Source and Research Integrity Verification Scenarios

------------------------------------------------------------------------

### 6.1 RA-SRC-001: External Research Source Access

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify controlled access to supported external research sources.

#### Expected Behavior

The Research Source Service shall:

-   access only configured research sources
-   return structured source results
-   preserve source identifiers and locations
-   report source access failures safely

#### Pass Criteria

Research source results are returned through the defined Research Source
interface without embedding source-specific behavior into the Research
Workflow.

------------------------------------------------------------------------

### 6.2 RA-SRC-002: Paper Metadata Retrieval

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify retrieval and normalization of available paper metadata.

#### Expected Behavior

The Paper Metadata Service shall preserve available:

-   title
-   authors
-   publication year
-   abstract
-   source identifiers

#### Pass Criteria

Available metadata is normalized correctly and missing metadata is
reported rather than invented.

------------------------------------------------------------------------

### 6.3 RA-SRC-003: Citation and Source Preservation

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that citation and source information remains associated with
generated research artifacts.

#### Expected Behavior

Research artifacts shall retain references to supporting research
sources.

#### Pass Criteria

Generated research findings can be traced to identifiable source
references.

------------------------------------------------------------------------

### 6.4 RA-SRC-004: Missing Source Information Handling

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify safe handling of incomplete or unavailable source information.

#### Expected Behavior

The Research Agent shall:

-   report unavailable information
-   preserve available metadata
-   avoid inventing missing source information
-   continue safely when partial results remain useful

#### Pass Criteria

No fabricated source or metadata values appear in the Research Result.

------------------------------------------------------------------------

### 6.5 RA-SRC-005: Multiple External Research Source Providers

#### Verification Layers

-   Unit
-   Integration

#### Objective

Verify that configured external research source providers can operate
individually and together through the Research Source abstraction.

#### Expected Behavior

The Research Source Service shall:

-   use only configured external research source providers
-   preserve provider-specific source identifiers and locations
-   combine usable results from multiple configured providers
-   continue safely when one configured provider fails and another
    provider returns usable results

#### Pass Criteria

Configured external research source providers operate through the
defined Research Source interface without requiring source-specific
behavior in the Research Workflow.

------------------------------------------------------------------------

### 6.6 RA-SRC-006: Mixed-Source Research Evaluation

#### Verification Layers

-   Unit
-   Integration

#### Objective

Verify that candidate papers from multiple external research source
providers can be evaluated together without losing source identity.

#### Expected Behavior

The Research Agent shall:

-   preserve each candidate paper source identifier exactly
-   associate evaluation results with supplied candidate papers
-   reject unknown or invented source identifiers
-   preserve source traceability across mixed-source results

#### Pass Criteria

Mixed-source candidate papers complete research evaluation with each
evaluation traceable to an identifiable supplied source reference.

------------------------------------------------------------------------

### 6.7 RA-SRC-007: Research Analysis Reference Validation

#### Verification Layers

-   Unit
-   Integration

#### Objective

Verify deterministic validation of context, paper, and candidate
research direction references.

#### Expected Behavior

The Research Agent shall:

-   verify that referenced context items exist
-   verify that referenced paper identifiers exist
-   verify candidate research direction context motivation and
    literature evidence unless explicitly marked speculative
-   reject unknown source identifiers

#### Pass Criteria

Invalid or unknown references are rejected and valid analysis remains
traceable to identifiable supporting evidence.

------------------------------------------------------------------------

## 7. AI Reasoning Verification Scenarios

------------------------------------------------------------------------

### 7.1 RA-AI-001: Reasoning Provider Integration

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify integration between Research Agent workflows and the configured
reasoning provider.

#### Expected Behavior

The system obtains reasoning results through the Project0 reasoning
abstraction.

#### Pass Criteria

A valid reasoning response is returned and processed.

------------------------------------------------------------------------

### 7.2 RA-AI-002: Unsupported Research Claim Prevention

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that the Research Agent does not present unsupported research
claims as source facts.

#### Test Scenario

Provide incomplete or insufficient research evidence for a requested
conclusion.

#### Expected Behavior

The Research Agent identifies insufficient evidence or distinguishes
generated analysis from supported source information.

#### Pass Criteria

Unsupported conclusions are not presented as established research facts.

------------------------------------------------------------------------

### 7.3 RA-AI-003: Invalid AI Output Handling

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify safe handling of unusable AI responses.

#### Expected Behavior

Invalid or incomplete responses are detected.

#### Pass Criteria

Invalid AI output does not produce an authoritative research artifact.

------------------------------------------------------------------------

### 7.4 RA-AI-004: Research Evaluation Retry Handling

#### Verification Layers

-   Unit
-   Integration

#### Objective

Verify bounded retry handling when a reasoning provider returns a
research evaluation response that violates required source traceability
or coverage constraints.

#### Expected Behavior

The Research Evaluation Service shall:

-   process candidate papers in bounded evaluation batches
-   detect an invalid or incomplete evaluation response within a batch
-   retry research evaluation once within the affected batch
-   accept a valid retry response
-   report the evaluation failure when the retry response remains
    invalid or incomplete

#### Pass Criteria

A valid retry response completes research evaluation successfully, and a
second invalid or incomplete response produces the expected evaluation
failure without additional retries.

------------------------------------------------------------------------

## 8. Research Artifact Compliance Verification

------------------------------------------------------------------------

### 8.1 RA-ART-001: Research Artifact Structure

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that generated Research Artifacts follow required structures.

#### Expected Behavior

Generated artifacts contain the required fields for their artifact type.

#### Pass Criteria

Research artifacts satisfy defined structural requirements.

------------------------------------------------------------------------

### 8.2 RA-ART-002: Research Artifact Source Traceability

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that generated Research Artifacts preserve supporting source
references.

#### Expected Behavior

Source-derived findings remain traceable to identifiable research
sources.

#### Pass Criteria

Research artifacts contain sufficient source information to support
human review.

------------------------------------------------------------------------

### 8.3 RA-ART-003: Saved Research Package Structure

#### Verification Layers

-   Unit
-   Integration
-   UI Acceptance where applicable

#### Objective

Verify the minimum structure of a saved research package.

#### Expected Behavior

The saved research package shall contain:

-   request
-   context summary
-   research strategy
-   retained papers
-   per-paper analyses
-   synthesis findings
-   candidate directions
-   provenance
-   validation status

#### Pass Criteria

The saved package contains the required information and preserves
supporting source traceability.

------------------------------------------------------------------------

## 9. Browser Acceptance Testing

Browser acceptance testing verifies that a real user can successfully
operate the Research Agent through the Project0 Dashboard.

Acceptance tests shall enter through the actual browser/UI boundary
rather than directly calling Project0 Python APIs.

The intended browser automation tool is Playwright for Python with
pytest. Initial coverage should use Chromium only.

Acceptance automation should be introduced incrementally. Individual UI
test cases use a case identifier while remaining mapped to the stable
verification scenario.

### 9.1 UI-RA-FUN-001-A: Research Agent Page Renders

#### Verification Scenario

`RA-FUN-001`

#### Purpose

Verify that the Research Agent request interface is accessible through
the Project0 Dashboard.

#### Preconditions

-   Project0 Dashboard is running at `127.0.0.1:8001`.
-   Playwright for Python is installed.
-   Playwright Chromium browser support is installed.

#### Test Steps

1.  Open `/agents/research` through Chromium.
2.  Locate the Research Agent heading.
3.  Locate the Research Question field.
4.  Locate optional research constraint controls where implemented.
5.  Locate optional Existing Research Context file selection/upload
    control where implemented.
6.  Locate the Submit Research Request button.

#### Expected Results

-   Research Agent page loads successfully.
-   Research Agent heading is visible.
-   Research Question field is visible.
-   Existing Research Context file selection/upload control is visible
    where implemented.
-   Submit Research Request button is visible.
-   No browser or application error prevents use of the request
    interface.

#### Automation File

``` text
test_research_agent_ui_request_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_001_research_agent_page_renders
```

### 9.2 UI-RA-FUN-001-B: Research Request Form Accepts Input

#### Verification Scenario

`RA-FUN-001`

#### Purpose

Verify that a user can enter a research question through the Research
Agent interface.

#### Preconditions

-   Project0 Dashboard is running at `127.0.0.1:8001`.
-   Research Agent request page is available.

#### Test Steps

1.  Open `/agents/research` through Chromium.
2.  Enter a research question.
3.  Enter optional research constraints where implemented.
4.  Read the entered values through the browser.

#### Expected Results

-   Research Question field accepts the entered request.
-   Optional constraint fields accept entered values where implemented.
-   Entered values remain unchanged.
-   No browser or application error prevents user input.

#### Automation File

``` text
test_research_agent_ui_request_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_001_research_request_form_accepts_input
```

### 9.3 UI-RA-FUN-001-C: Research Request Submission Starts Processing

#### Verification Scenario

`RA-FUN-001`

#### Purpose

Verify that a user can submit a valid Research Agent request through the
browser interface.

#### Preconditions

-   Project0 Dashboard is running.
-   Research Agent request page is available.
-   Supported external research sources are available when required.
-   The configured reasoning provider is available when required.

#### Test Steps

1.  Open `/agents/research`.
2.  Enter a valid research question.
3.  Click Submit Research Request.
4.  Observe the request interface immediately after submission.

#### Expected Results

-   The submit action is accepted.
-   The Submit Research Request button changes to the Processing state
    where implemented.
-   The visible processing indicator is displayed where implemented.
-   The browser remains within the Research Agent workflow.
-   No immediate browser or application error is displayed.

#### Automation File

``` text
test_research_agent_ui_request_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_001_research_request_submission_starts_processing
```

### 9.4 UI-RA-FUN-003-A: Candidate Research Results Are Presented

#### Verification Scenario

`RA-FUN-003`

#### Purpose

Verify that a submitted research request produces visible candidate
research results through the browser interface.

#### Preconditions

-   Project0 Dashboard is running.
-   A valid Research Agent request can be processed.
-   Supported external research sources are available.

#### Test Steps

1.  Submit a valid research request through the browser.
2.  Wait for the Research Agent workflow to produce candidate results.
3.  Inspect the research results page.

#### Expected Results

-   Candidate research papers are displayed.
-   Available paper metadata is displayed.
-   Source information is displayed.
-   Relevance information is displayed where available.
-   No unsupported candidate reference is presented as a retrieved
    source.

#### Automation File

``` text
test_research_agent_ui_results_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_003_candidate_research_results_are_presented
```

### 9.5 UI-RA-SRC-003-A: Research Results Display Source Information

#### Verification Scenario

`RA-SRC-003`

#### Purpose

Verify that research results presented through the browser preserve
source traceability.

#### Preconditions

-   Project0 Dashboard is running.
-   A Research Agent request has produced research results.

#### Test Steps

1.  Submit a valid research request.
2.  Wait for research results.
3.  Inspect displayed paper source information.

#### Expected Results

-   Source information is visible for retrieved papers.
-   Source information remains associated with the appropriate research
    result.

#### Automation File

``` text
test_research_agent_ui_results_acceptance.py
```

#### Automation

``` text
test_UI_RA_SRC_003_research_results_display_source_information
```

### 9.6 UI-RA-FUN-009-A: Research Request Can Be Revised

#### Verification Scenario

`RA-FUN-009`

#### Purpose

Verify that a user can revise a Research Agent request through the
browser workflow.

#### Preconditions

-   Project0 Dashboard is running.
-   A Research Agent request has produced a reviewable result.

#### Test Steps

1.  Submit a valid research request.
2.  Wait for the research result.
3.  Select Revise where implemented.
4.  Modify or append research instructions.
5.  Resubmit the revised request.
6.  Wait for the revised result.

#### Expected Results

-   The original research request remains available.
-   Applicable research constraints remain available.
-   Revised instructions are accepted.
-   The revised request executes through the standard Research Workflow.
-   Applicable source and citation information is preserved.

#### Automation File

``` text
test_research_agent_ui_revision_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_009_research_request_can_be_revised
```

### 9.7 UI-RA-FUN-001-D: Visible Research Workflow Result Is Presented

#### Verification Scenario

`RA-FUN-001`

#### Purpose

Verify that the browser displays a clear final Research Result.

#### Preconditions

-   Project0 Dashboard is running.
-   A Research Agent request can complete successfully.

#### Test Steps

1.  Submit a valid research request.
2.  Wait for workflow completion.
3.  Inspect the visible completion information.

#### Expected Results

-   A clear Research Result is displayed.
-   Completion status and summary information are visible where
    implemented.
-   Research artifacts are accessible where implemented.
-   The browser does not remain indefinitely in the Processing state.

#### Automation File

``` text
test_research_agent_ui_request_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_001_visible_research_workflow_result_is_presented
```

### 9.8 UI-RA-FUN-010-A: Existing Research Context Can Be Selected

#### Verification Scenario

`RA-FUN-010`

#### Purpose

Verify that a user can select a supported Existing Research Context
document through the Research Agent interface.

#### Preconditions

-   Project0 Dashboard is running.
-   Research Agent request page is available.
-   A supported text-based context document is available.

#### Test Steps

1.  Open `/agents/research`.
2.  Select a supported Existing Research Context document.
3.  Submit a research request.
4.  Wait for workflow completion.
5.  Inspect the resulting context and research output.

#### Expected Results

-   The selected context document is accepted.
-   Context-derived information is presented where implemented.
-   Context provenance is preserved.
-   The workflow does not require repository storage of the selected
    source document.
-   No context extraction or analysis error is silently ignored.

#### Automation File

``` text
test_research_agent_ui_context_acceptance.py
```

#### Automation

``` text
test_UI_RA_FUN_010_existing_research_context_can_be_selected
```

Playwright automatic waiting should be preferred over arbitrary sleep
calls because external research source and local reasoning execution
time may vary. Project0 `--ui-slowmo` may be used to slow headed browser
actions for human observation, but it shall not be used for
synchronization or alter expected results.

------------------------------------------------------------------------

## 10. Exploratory AI Testing

Real local-model testing remains separate from deterministic automated
acceptance testing.

Exploratory AI testing may require human judgment for:

-   research relevance
-   semantic relevance ranking quality
-   factual grounding
-   paper summary usefulness
-   research comparison quality
-   unsupported claims
-   hallucination detection
-   research gap usefulness
-   experiment suggestion quality
-   Existing Research Context interpretation quality
-   per-paper technical analysis quality
-   cross-paper synthesis quality
-   candidate research direction usefulness and evidence grounding

Real Ollama/qwen2.5:7b execution should therefore complement, rather
than replace, deterministic unit, integration, and browser acceptance
testing.

External research source behavior should be deterministic or controlled
during automated testing where practical so that changing external
search results do not make regression tests unreliable.

------------------------------------------------------------------------

## 11. Platform Boundary Tests

------------------------------------------------------------------------

### 11.1 RA-ARCH-001: Agent and Platform Separation

#### Verification Layers

-   Integration
-   UI Acceptance where applicable

#### Objective

Verify that Research Agent responsibilities remain separate from
Project0 platform responsibilities.

#### Expected Behavior

The Research Agent uses reusable Project0 services without redefining
platform ownership.

#### Pass Criteria

No Research Agent-specific responsibilities are embedded into shared
platform components.

------------------------------------------------------------------------

### 11.2 RA-ARCH-002: External Source Isolation

#### Verification Layers

-   Unit
-   Integration

#### Objective

Verify that external research source-specific behavior remains isolated
behind Research Source interfaces.

#### Expected Behavior

Research Workflow components depend on Research Source interfaces rather
than source-specific implementations.

#### Pass Criteria

External research source implementations can be replaced without
modifying Research Workflow responsibilities.

------------------------------------------------------------------------

## 12. Regression Criteria

The Research Agent is considered stable when:

-   automated unit tests pass
-   integration tests pass
-   required browser acceptance scenarios pass
-   source and citation preservation behavior is verified
-   research artifact validation passes
-   Existing Research Context and provenance validation passes
-   per-paper and Research Direction Analysis validation passes
-   no-context backward compatibility is verified
-   Project0 platform regression tests remain passing

Research Agent implementation shall not regress the established Project0
platform and Documentation Agent test baseline.

------------------------------------------------------------------------

## 13. Completion Criteria

The Research Agent may be considered complete when:

### Functional

-   Research requests process successfully.
-   Research strategies are generated correctly.
-   Deterministic research search terms are generated correctly.
-   Relevant candidate papers can be discovered.
-   Paper metadata can be retrieved and normalized.
-   Research relevance evaluation and score normalization operate
    correctly.
-   Highest-relevance papers are retained according to the configured
    maximum result count while discovered source references are
    preserved.
-   Structured research artifacts are generated.
-   Optional Existing Research Context processing operates correctly.
-   Structured per-paper analyses are generated correctly.
-   Research Direction Analysis produces required synthesis findings and
    evidence-grounded candidate directions.
-   Existing workflow behavior is preserved when no context document is
    provided.

### Research Integrity

-   Source and citation information is preserved.
-   Missing source information is not invented.
-   Source facts remain distinguishable from generated analysis.
-   Unsupported research claims are handled safely.
-   Context and paper provenance is preserved.
-   Referenced context items and paper identifiers are valid.
-   Candidate research directions preserve required context motivation
    and literature evidence unless explicitly marked speculative.
-   Source-derived context findings, source-derived per-paper
    interpretation, and Research Agent inference remain distinguishable.

### Architecture

-   Platform boundaries are preserved.
-   Agent responsibilities remain isolated.
-   External source-specific behavior remains behind defined interfaces.

### Documentation

-   Research Agent documentation set is complete.
-   Documentation standards are followed.
-   Acceptance results are recorded.

------------------------------------------------------------------------

## 14. Future Extensions

Future versions may include:

-   Expanded Playwright browser acceptance testing
-   Research quality metrics
-   Expanded AI evaluation scenarios
-   Additional external research sources
-   Semantic research retrieval testing
-   Vector-based knowledge search testing
-   Multi-agent research workflow testing
-   Automated acceptance execution
-   Agent comparison testing
-   OCR context-document testing when OCR support is introduced
