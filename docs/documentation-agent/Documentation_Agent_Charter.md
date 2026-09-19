# Documentation Agent Charter

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-19

## 1. Purpose and Objectives

The Project0 Documentation Agent provides an AI-assisted, human-controlled capability for synchronizing existing Markdown documentation with repository implementation. It identifies material gaps, proposes accurate and minimal updates, and applies only individually approved changes while making repository-grounded documentation maintenance part of the normal development workflow.

The agent shall:

- Treat supplied repository content as authoritative evidence and target documentation as a controlled artifact.
- Identify material gaps and produce concrete, minimal, style-preserving Markdown proposals with a rationale.
- Restrict proposals to permitted existing Markdown targets.
- Present focused differences, warnings, and errors for human review.
- Filter source-grounded exact-claim replacements or insertions that merely restate existing information, expose private implementation details, misrepresent already named identifiers as standalone response documentation, or destructively collapse an established contract enumeration; assign uniquely verified anchors deterministically and use model output only for bounded replacement wording or multi-claim disambiguation.
- Support approve, revise, reject, and skip decisions for each proposal and apply only individually approved changes.
- Validate affected documentation at the implemented workflow stages and provide a final Git diff.
- Reuse generic Project0 services while keeping agent-specific behavior outside shared platform components.

Detailed behavior and contracts remain defined by the Documentation Agent Functional Specification, Architecture, Design, Interface Design, Test Plan, Test Results, and Testing Guide. Repository-wide documentation requirements remain governed by Documentation Standards, while project-wide mission and principles remain governed by the Project Charter.

## 2. Scope and Boundaries

### Included

- Existing Markdown documentation in the configured local Git repository.
- A required request with optional target-document and authoritative-source paths.
- Repository-grounded context construction and provider-neutral structured reasoning.
- Two-stage source-grounded gap analysis and compact exact-claim proposal generation when source paths are supplied, or single-stage proposal generation otherwise.
- Deterministic safeguards for paths, content form, locations, sections, anchors, and Python declarations.
- File-specific proposals, preliminary validation, individual review, atomic application, final validation, Git diff generation, and Dashboard presentation.

### Excluded

- Creating or deleting documentation through the executable proposal workflow.
- Modifying source code, tests, configuration, or non-Markdown files.
- Applying changes without explicit approval or outside repository and target boundaries.
- Committing, pushing, merging, branching, or opening pull requests.
- Persistent review state, transactional rollback, automatic regeneration after revision, continuous monitoring, or unsupported model-memory evidence.
- Placing Documentation Agent business logic in the shared Dashboard Framework.

Shared reasoning models can represent create and delete operations, but the current executable Documentation Workflow accepts only updates to existing `.md` files.

### Human authority and repository safety

Each proposal is reviewed independently. `approve` authorizes immediate application; compatible approvals for the same file are sequenced in review order against successful writes owned by the current workflow, while external or conflicting changes remain fail-closed. `reject` and `skip` perform no write; `revise` retains state and returns the original request fields for revision and resubmission. Earlier approved proposals may be written while later proposals remain under review, so the proposal set is human-controlled but not transactional.

Executable proposals are limited to existing permitted Markdown files. Each proposal retains the original document snapshot; stale approved changes are refused; successful writes use temporary files and atomic replacement; unapplied or failed proposals remain unchanged; and failures are reported explicitly. AI reasoning recommends changes but has no independent repository authority.

## 3. Operating Principles

- **Repository Grounding:** Explicit source paths are read-only evidence and target Markdown is the controlled artifact; model output is not authoritative.
- **Human-in-the-Loop:** Every accepted proposal requires an individual decision, and only approval authorizes a write.
- **Minimum Necessary Change:** Preserve unrelated content, structure, terminology, and formatting.
- **Fail-Closed Synchronization:** Skip and warn when scope, location, semantics, content form, or reproduced source declarations cannot be established reliably.
- **Deterministic Before AI:** Use deterministic services for repository access, enforcement, validation, application, and diff generation; use AI where interpretation or wording is required.
- **Explicit Validation Boundaries:** Preliminary validation checks current proposal targets; final validation checks successfully written paths and reports defects without rolling back completed writes.
- **Modular Architecture:** Separate agent workflow and presentation from shared services through defined interfaces and models.
- **Provider Abstraction:** Use a provider-neutral reasoning contract supporting configured Ollama or deterministic stub behavior.
- **Documentation by Default:** Maintain documentation as living project knowledge under Project0 Documentation Standards.

The Documentation Agent is Project0's initial reference implementation for a human-reviewed specialized-agent workflow. This role does not make its behavior mandatory for later agents.

## 4. Success Criteria

The Documentation Agent is successful when it can:

- Distinguish material gaps from unsupported or immaterial observations.
- Generate concrete edits grounded in supplied evidence and confined to permitted Markdown paths.
- Preserve unrelated content and established style.
- Present clear rationales and focused differences.
- Correctly honor every supported review decision and apply only approved, non-stale proposals.
- Fail closed when proposals cannot be located or grounded reliably.
- Report validation at its actual implemented boundaries and produce an accurate Git diff.
- Surface warnings and failures without claiming unsupported success.
- Operate through reusable Project0 services without transferring agent responsibilities into shared platform components.

Success does not require automatic publication, autonomous monitoring, persistent recovery, transactional rollback, or other future capabilities not implemented and tested.
