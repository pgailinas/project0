# Documentation Agent Charter

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

Establish the mission, scope, operating principles, authority
boundaries, and success criteria for the Project0 Documentation Agent.

The Documentation Agent exists to help synchronize Markdown
documentation with repository implementation while minimizing manual
effort and preserving documentation quality through controlled,
reviewable updates.

This charter defines the agent's high-level intent and governing
boundaries. Detailed behavior, architecture, component design, and
interfaces are defined in their respective authoritative documents.

---

## 2. Mission

Provide an AI-assisted, human-controlled capability that compares
selected documentation with repository evidence, identifies material
documentation gaps, proposes accurate and minimal updates, and applies
only individually approved changes to existing Markdown files.

The Documentation Agent supports Project0's broader mission of using
specialized AI agents within structured development workflows while
preserving human decision authority and professional software
engineering practices.

---

## 3. Vision

Make accurate, current, repository-grounded documentation a normal and
integrated part of software development rather than a separate manual
maintenance activity.

The Documentation Agent demonstrates how a specialized Project0 agent
can combine deterministic platform services, structured AI reasoning,
validation, and human approval checkpoints within a reusable AI-native
development framework.

---

## 4. Objectives

The Documentation Agent shall:

- Use supplied repository content as authoritative evidence for
  source-grounded documentation synchronization.
- Treat target documentation as a controlled artifact rather than
  regenerating it without regard for its existing structure.
- Identify material gaps between selected documentation and selected
  authoritative source files.
- Produce concrete, minimal, style-preserving Markdown proposals.
- Explain the rationale for each proposed documentation change.
- Restrict proposals to permitted, existing Markdown target files.
- Present focused differences and workflow warnings for human review.
- Support approve, revise, reject, and skip decisions for each
  proposal.
- Apply only individually approved changes.
- Validate affected documentation at the implemented workflow stages.
- Provide a final Git diff for applied changes.
- Reuse generic Project0 platform services and interfaces where
  practical.
- Preserve separation between reusable Project0 infrastructure and
  Documentation Agent-specific behavior.

---

## 5. Scope

### In Scope

The current Documentation Agent supports:

- Existing Markdown documentation in the configured local Git
  repository.
- A required documentation request with optional target-document and
  authoritative-source paths.
- Repository-grounded context construction.
- Provider-neutral, structured AI reasoning.
- A two-stage gap-analysis and proposal process when authoritative
  source paths are supplied.
- A single proposal-generation stage when no source paths are supplied.
- Source-grounded proposal safeguards, including path, content-form,
  location, section-alignment, anchor, and Python-declaration checks.
- File-by-file documentation proposals.
- Preliminary validation of proposal target paths before review.
- Individual human review of each proposal.
- Controlled and atomic application of approved updates.
- Final validation of successfully applied paths.
- Git diff generation for applied paths.
- Workflow summaries, warnings, errors, and Dashboard presentation.

### Out of Scope

The current Documentation Agent does not:

- Create or delete documentation files through the executable
  proposal workflow.
- Modify application source code, tests, configuration, or other
  non-Markdown files.
- Apply a proposal without an explicit approve decision.
- Modify paths outside the configured repository or explicit target
  scope.
- Commit, push, merge, create branches, or open pull requests.
- Persist workflow review state across process restarts.
- Provide transactional rollback when final validation fails.
- Automatically regenerate a revised proposal after a revise decision.
- Operate as a continuously monitoring repository service.
- Treat model memory or unsupported inference as repository evidence.
- Place Documentation Agent business logic inside the shared Dashboard
  Framework.

Although shared reasoning models can represent create and delete
operations, the current Documentation Workflow accepts only updates to
existing `.md` files.

---

## 6. Operating Principles

The Documentation Agent follows these principles:

- **Repository Grounding**: For source-grounded work, explicitly
  supplied source paths are read-only authoritative evidence and target
  Markdown is the controlled artifact. Model output is not itself
  authoritative.

- **Human-in-the-Loop**: Every accepted proposal requires an individual
  review decision. Only approval authorizes a repository write.

- **Minimum Necessary Change**: Updates should preserve unrelated
  content, structure, terminology, and formatting.

- **Fail-Closed Synchronization**: A source-grounded proposal is skipped
  with a warning when its scope, location, semantics, content form, or
  reproduced source declaration cannot be established reliably.

- **Deterministic Before AI**: Repository access, path enforcement,
  proposal safeguards, validation, application, and diff generation use
  deterministic services. AI reasoning is used where interpretation or
  documentation wording is required.

- **Explicit Validation Boundaries**: Preliminary validation evaluates
  the current proposal target paths before review. Final validation
  evaluates successfully applied paths after writing. Final validation
  reports defects but does not roll back a completed write.

- **Modular Architecture**: Agent-specific workflow and presentation
  behavior remain separate from shared platform services and communicate
  through defined interfaces and models.

- **Provider Abstraction**: Documentation reasoning uses a
  provider-neutral service contract. Current runtime configuration may
  select local Ollama or deterministic stub behavior without redefining
  the agent's charter.

- **Documentation by Default**: Documentation is living project
  knowledge and should remain aligned with implementation under the
  Project0 Documentation Standards.

---

## 7. Relationship to Project0

The Documentation Agent is a specialized agent operating within the
Project0 AI-native software development framework.

Project0 supplies reusable repository access, context construction,
reasoning abstraction, artifact location, validation, workflow,
repository-update, Git-diff, platform-dispatch, skill-registry, and
Dashboard capabilities. The Documentation Agent composes these services
into a documentation-specific workflow rather than redefining their
shared responsibilities.

The Dashboard Framework owns the common application shell, navigation,
and Work Area hosting. Documentation Agent routes, view models, UI
mapping, and agent-specific presentation remain within the Documentation
Agent package.

The Documentation Agent serves as Project0's initial reference
implementation for a human-reviewed specialized-agent workflow. This
role does not make Documentation Agent-specific behavior a requirement
for every later Project0 agent.

---

## 8. Human Authority and Repository Safety

Repository modification is a controlled action.

For each proposal:

- `approve` authorizes immediate application of that proposal;
- `reject` records the decision and performs no write;
- `skip` records the decision and performs no write; and
- `revise` retains workflow state and returns the original request
  fields for user revision and resubmission.

The agent additionally shall:

- Restrict executable proposals to existing Markdown files within the
  repository and, when supplied, the explicit target allowlist.
- Preserve a snapshot of the original document in each proposal.
- Refuse an approved change if the document has changed since proposal
  creation.
- Apply successful changes through a temporary file and atomic
  replacement.
- Leave rejected, skipped, revised, invalid, and out-of-scope proposals
  unapplied.
- Report skipped proposals, application failures, and validation
  failures rather than silently treating them as success.
- Generate a final Git diff when at least one path is successfully
  applied.

Approval occurs one proposal at a time. Earlier approved proposals may
already be written while later proposals remain under review. The
workflow is therefore human-controlled but not transactional across the
complete proposal set.

AI reasoning recommends documentation changes but does not independently
possess authority to modify the repository.

---

## 9. Success Criteria

The Documentation Agent is successful when it can:

- Distinguish material documentation gaps from unsupported or
  non-material observations.
- Generate concrete edits only for gaps established by supplied source
  evidence during source-grounded synchronization.
- Keep proposal paths within the permitted Markdown scope.
- Preserve unrelated document content and established style.
- Provide a clear rationale and focused difference for each proposal.
- Require and correctly honor every supported review decision.
- Apply only approved and non-stale proposals.
- Fail closed when a proposal cannot be located or grounded reliably.
- Report preliminary and final validation results at their actual
  implemented boundaries.
- Produce an accurate Git diff for applied documentation paths.
- Surface warnings and failures without claiming unsupported success.
- Operate through reusable Project0 services without transferring
  Documentation Agent responsibilities into shared platform components.

Success does not require automatic publication, autonomous repository
monitoring, persistent workflow recovery, or rollback behavior that the
current implementation does not provide.

---

## 10. Future Direction

Future evolution may improve the Documentation Agent without changing
its repository-grounded and human-controlled principles. Potential
directions include:

- Durable workflow and review-state persistence.
- More capable revision and proposal-regeneration workflows.
- Transactional or explicit rollback support.
- Controlled creation and deletion of documentation files.
- Improved documentation impact analysis and semantic retrieval.
- Larger coordinated multi-document updates.
- Additional reasoning providers and deterministic validators.
- Improved proposal, validation, and diff presentation.
- Optional repository-event awareness and automation that retains
  defined human authority.

These are possible future capabilities, not claims about the current
implementation. They require corresponding implementation, tests, and
updates to the appropriate specification and design documents before
being treated as available behavior.

---

## 11. Document Authority

This charter governs the high-level purpose, mission, scope, operating
principles, and authority boundaries of the Documentation Agent.

The **Documentation Agent Functional Specification** defines detailed
supported behavior and requirements.

The **Documentation Agent Architecture** defines high-level component
organization and responsibility boundaries.

The **Documentation Agent Design** and **Documentation Agent Interface
Design** define internal behavior, interactions, models, and interfaces.

The **Documentation Agent Test Plan**, **Test Results**, and **Testing
Guide** define intended coverage, recorded evidence, and verification
procedures without superseding implementation or tests.

Repository-wide documentation requirements are governed by
**Documentation Standards**, and project-wide mission and principles are
governed by the **Project Charter**.

For statements about current executable behavior, source code and
automated tests are authoritative. Conflicts among implementation,
tests, and documentation should be identified and resolved explicitly
rather than silently redefining the agent's behavior or authority.

---

**End of Document**
