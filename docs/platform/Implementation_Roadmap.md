# Implementation Roadmap

**Version:** 0.9  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## Purpose and Authority

This roadmap records Project0's phased implementation history, delivery
sequence, current corrective priorities, and possible future expansion. It is
not authority for current implementation or test success. Repository-visible
state belongs in [Implementation Status](Implementation_Status.md), and a
phase's presence in source does not prove that its tests or acceptance criteria
pass at the current commit.

Phases are historical planning boundaries. Improvements to earlier capabilities
do not require new phase numbers.

## Current or Planned State

Project0 develops small, testable vertical capabilities using typed modular
interfaces, deterministic processing where model reasoning is unnecessary,
dependency injection and test substitutes, human review before Documentation
Workflow writes, separation of agent behavior from shared services,
source-grounded documentation, and continuous validation.

| Phase | Name | Repository-visible state at the pinned audit commit |
| --- | --- | --- |
| 1 | Foundation | Implemented |
| 2 | Core Platform Services | Implemented |
| 3 | Repository Knowledge Services | Implemented with in-memory, non-semantic retrieval |
| 4 | AI Reasoning Integration | Implemented for Ollama and deterministic stubs |
| 5 | Validation Services | Implemented; default workflow omits Documentation Consistency |
| 6 | Workflow Integration | Implemented for Documentation review/update and Git differences |
| 7 | Dashboard Framework | Implemented with shared limitations |
| 8 | Documentation Agent User Interface | Implemented |
| 9 | Testing and Verification | Test layers exist; pinned-commit result not established |
| 10 | Platform Validation Consolidation | Partially realized; no separate Platform Test Plan |
| 11 | Research Agent Foundation and Functional Validation | Implemented |
| 12 | Documentation Agent Enhancement | Implemented |
| 13 | Research Agent Context-Aware Literature Analysis | Implemented |
| 14 | Project0 Agent Skills Foundation | Implemented; repository verification incomplete |

The phase state is intentionally more precise than the earlier blanket term
“completed.” Current source contains work corresponding to every phase, but the
pinned audit identified repository-level gaps and did not establish an
all-phases-passing result.

### Phase outcomes

1. **Foundation** established package metadata, `src` layout, MkDocs
   documentation, settings, logging, startup validation, and project guidance.
2. **Core Platform Services** added repository access, generic sequential
   workflow execution, deterministic context building, typed contracts, and
   dispatcher composition.
3. **Repository Knowledge Services** added Markdown parsing, in-memory indexing,
   deterministic selection, bounded context, and Knowledge Service processing.
4. **AI Reasoning Integration** added provider-neutral structured requests,
   schema-driven prompting, Ollama, stubs, parsing, and validation.
5. **Validation Services** added Markdown, link, strict MkDocs, documentation
   consistency, aggregation, and exception isolation.
6. **Workflow Integration** added source-grounded documentation reasoning,
   proposal review, constrained updates, stale/path/anchor safeguards, final
   validation, and Git differences.
7. **Dashboard Framework** added the FastAPI/Jinja2 shell, status/navigation,
   agent registration, routes, static assets, and fallback behavior.
8. **Documentation Agent UI** exposed request, proposal, difference, validation,
   decision, and completion flows through agent-owned presentation layers.
9. **Testing and Verification** organized unit, integration, and browser test
   sources, deterministic stubs, and reusable commands.
10. **Platform Validation Consolidation** separated platform and agent test
    ownership and added platform guidance, a UI status record, and integration
    coverage, but not the originally named separate Platform Test Plan.
11. **Research Agent Foundation** added research contracts, services, source
    adapters, workflows, Dashboard integration, and agent tests.
12. **Documentation Agent Enhancement** added explicit source/target context,
    two-stage reasoning, localized proposals, and deterministic safeguards.
13. **Context-Aware Literature Analysis** added optional context ingestion,
    provenance, bounded multi-query retrieval, evidence acquisition, paper
    analysis, synthesis, and grounded Direction Analysis.
14. **Agent Skills Foundation** added repository-local skills, immutable models,
    discovery/loading, prompt propagation, dispatcher assembly, and strict
    Documentation Workflow skill selection.

Phase details remain bounded by current implementation: state and indexes are
in memory; providers and browser tests require their environments; automatic
Git/publication operations, external skill lifecycle management, and dynamic
registration are absent; the Dashboard phase is stale; and implemented
Documentation Consistency is not a default workflow validator.

## Evidence and Dependencies

The implemented dependency direction is:

1. configuration and startup validation;
2. shared models and protocols;
3. repository, context, knowledge, reasoning, artifact, skill, and validation
   services;
4. generic and agent-specific workflow coordinators;
5. Platform Dispatcher composition;
6. agent UI services and routers; and
7. Dashboard composition and presentation.

Repository access precedes analysis; deterministic context precedes grounded
reasoning; provider-neutral boundaries precede agent model use; validation and
controlled updates precede reviewed writes; shared Dashboard infrastructure
precedes agent UI integration; and deterministic tests precede live-provider
validation. Agent workflows may depend on shared services, but shared services
must not acquire agent-specific UI or domain responsibilities.

Verification combines focused unit tests, assembled integration tests, browser
acceptance, strict documentation builds, source compilation, optional live
checks, and final source/documentation/status consistency review. Results must
identify the exact source state and environment; historical counts, unavailable
tools, skips, and live checks remain explicitly bounded.

## Gaps and Priorities

Corrective priorities supported by the pinned audit are:

1. Remove Markdown fences from `knowledge_interfaces.py` and restore clean
   compilation.
2. Decide whether Documentation Consistency is a default Documentation Workflow
   validator, then align source, tests, and documentation.
3. Derive the Dashboard phase from an authoritative source.
4. Define the browser-acceptance dependency and browser-installation procedure.
5. Populate or remove empty test modules.
6. Re-run compilation, pytest, and strict MkDocs and record exact results.
7. Add CI only after its supported environment and gates are defined.

Potential future work—not current capability or a committed schedule—includes
semantic/vector retrieval; durable workflow, review, research, and audit state;
asynchronous/distributed workflows; more reasoning providers and agents;
expanded validation, security, performance, and benchmarking; shared Research
Agent skill selection; external skill trust, installation, distribution, and
lifecycle management; dynamic registration; authentication and roles;
deployment automation; and CI/CD.

The baseline is verified only when component contracts and applicable
deterministic workflows pass; repository writes preserve review and safety;
supported browser scenarios pass; documentation validation and compilation are
clean; evidence records identify the validated commit/environment; known gaps
are resolved or accepted; and source, tests, configuration, templates, and
documentation remain aligned.

## Update Rules

- Add a future phase only when its scope, ownership, dependencies, deliverables,
  and validation criteria are sufficiently defined.
- Keep phase names and numbering aligned with Implementation Status.
- Record delivery without converting it into an unverified completion claim.
- Move verified current-state detail to Implementation Status and retain only
  the planning context needed here.
- Keep future possibilities clearly separate from committed work.
- Preserve historical phase intent when refining current priorities.
