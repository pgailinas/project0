# Development Standards

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose and Scope

This document defines the engineering standards for designing, implementing, testing, documenting, and reviewing Project0 changes. The standards apply to human- and AI-assisted work across the shared platform, Dashboard, Documentation Agent, Research Agent, tests, and repository documentation.

The goals are to support:

- maintainable architecture;
- controlled complexity;
- clear engineering decisions;
- safe and minimal change;
- effective human and AI collaboration;
- deterministic validation; and
- reliable software evolution.

Current repository source, tests, configuration, templates, and documentation provide the implementation context for these standards. Where a standard and the implementation differ, record the discrepancy rather than describing an unimplemented convention as current behavior.

## 2. Core Engineering Principles

### 2.1 Reuse Proven Solutions

Reuse proven solutions whenever practical. Introduce novel technology, frameworks, patterns, or custom infrastructure only when they solve a demonstrated problem or provide measurable value.

### 2.2 Every Component Must Earn Its Place

Before adding a service, library, abstraction, agent capability, provider, or infrastructure dependency, identify:

- the problem being solved;
- why existing components are insufficient;
- the expected benefit;
- the integration and operational cost; and
- how the new capability will be tested and maintained.

Components without a clear responsibility or benefit increase coupling and maintenance cost.

### 2.3 Select Technology on Engineering Merit

Evaluate technology against Project0 requirements, maturity, maintainability, stability, community support, integration complexity, licensing, security, and operational impact. Prefer mature open-source components unless a commercial component offers a clear advantage that justifies its cost and dependency.

### 2.4 Design Before Implementation

Establish the design boundary before writing production code. The design should identify, at the level appropriate to the change:

- responsibilities and ownership;
- public interfaces and data contracts;
- control and data flow;
- dependencies;
- error and degraded-mode behavior;
- state and persistence boundaries;
- security constraints; and
- unit, integration, and acceptance validation.

The amount of design should match the change. A localized defect does not require a new architecture document, while a new workflow or shared component requires an explicit contract.

### 2.5 Maintain Shared Language

Project0 uses AI-assisted engineering. Terms, model names, statuses, component ownership, and architectural decisions must be stated consistently in source and documentation. Shared language reduces ambiguity for both human contributors and AI tools.

### 2.6 Prefer Explicit, Understandable Systems

Favor simple designs, typed contracts, explicit dependencies, bounded workflows, and readable implementations over implicit behavior or speculative abstraction. Complexity is acceptable only when its value is visible and testable.

## 3. Sources of Truth and Change Grounding

### 3.1 Repository Ground Truth

For implementation work, inspect the current target branch or supplied repository baseline before proposing changes. Source, tests, configuration, templates, and dependency declarations are authoritative for implemented behavior. Do not assume a class, route, option, provider, field, test, or workflow exists without verifying it.

For documentation synchronization, implementation and automated tests override stale prose. Historical documents can supply intent, but unsupported claims must not be preserved merely because they already exist.

### 3.2 Supplied-File or Strict-Mode Ground Truth

When a task explicitly supplies files as the modification baseline:

- treat those exact files as authoritative within the task's stated scope;
- do not silently substitute a different checkout or remembered version;
- inspect all supplied dependencies needed to validate the requested change;
- preserve unrelated content and existing structure; and
- report when the supplied files are insufficient or conflict with the designated repository authority.

“Strict mode” does not make an isolated file globally authoritative over its actual dependencies. It constrains the edit baseline and scope while requiring verified compatibility with the evidence the user designated.

### 3.3 Evidence Before Assumption

Before adding or changing code, verify:

- referenced names exist and are in scope;
- imports and package boundaries are correct;
- parameters, return types, enums, and status values match their consumers;
- routes, templates, CSS, and view models agree where UI behavior is involved;
- environment variables and defaults match configuration source;
- filesystem paths are resolved and validated consistently; and
- tests exercise the relevant public behavior.

If evidence is incomplete, state the uncertainty or request the missing source rather than inventing behavior.

## 4. Architecture and Interface Standards

### 4.1 Single, Clear Responsibility

Each component should own one coherent responsibility. Avoid duplicate behavior, hidden dependencies, cross-layer shortcuts, and excessive coupling.

Keep shared platform responsibilities separate from agent-specific workflow and interface behavior. Agent-specific services belong in their agent package unless the capability is demonstrably reusable.

### 4.2 Interface-First Boundaries

Define behavior at public boundaries before binding callers to a concrete implementation. Project0 uses typed `Protocol` interfaces for workflow, repository, context, reasoning, validation, artifact, and Research services. New interfaces should be introduced when they establish a useful substitutable boundary—not merely to wrap one implementation without benefit.

Public interfaces should specify:

- accepted inputs;
- returned models;
- observable state transitions;
- expected failure behavior; and
- ownership of side effects.

Implementation details remain internal unless callers depend on them.

### 4.3 Dependency Injection

Pass collaborators into services, workflows, and UI adapters where practical. Dependency injection should make deterministic substitutes possible and prevent production services from being constructed inside domain logic. Assembly belongs at composition boundaries such as the Platform Dispatcher and executable Dashboard factory.

### 4.4 Data Models and Status Values

Use typed shared models for cross-component data. Follow current Project0 patterns where appropriate:

- dataclasses for request, result, state, and value objects;
- `frozen=True` and `slots=True` for stable shared records;
- tuples for stable collections;
- `StrEnum` for contract values; and
- explicit optional fields rather than sentinel strings.

Do not introduce a generic envelope or base model unless multiple implemented consumers need it. Preserve exact enum strings and field meanings because they are part of the contract.

### 4.5 Workflow Ownership and Observability

Do not assume every workflow uses the generic Workflow Engine. The generic context workflow, stateful Documentation Workflow, and Research Workflow have distinct orchestration and result contracts.

Workflow implementations should make it possible to determine:

- the workflow identifier and status;
- the current or terminal boundary;
- completed and failed stages;
- warnings and error information;
- the expected next action when review or recovery is possible;
- what state is retained; and
- whether state is in-memory or durable.

Logs and result models should identify the first meaningful failure boundary rather than only presenting a final generic error.

### 4.6 Incremental Capability Growth

New functionality must build on current architecture, preserve unrelated behavior, include appropriate tests, update affected documentation, and record material design decisions. Avoid architecture changes hidden inside defect fixes.

## 5. Code Standards

### 5.1 Python and Package Structure

- Support Python 3.12 or later, as declared in `pyproject.toml`.
- Keep production code under `src/project0/` and use absolute `project0...` imports across package boundaries.
- Execute installed modules with `python -m ...`; do not rely on direct execution of files within the `src` tree.
- Add new dependencies to `pyproject.toml` and install from repository metadata rather than documenting ad hoc manual installation as the normal path.

### 5.2 Source File Headers

Python source files must begin with the standard Project0 header identifying the owning component, filename, and concise purpose. Follow the exact header definition in [Documentation Standards](Documentation_Standards.md).

### 5.3 Type Contracts

- Type public parameters and return values.
- Use `Protocol` for meaningful substitutable service boundaries.
- Prefer explicit domain types and enums over unvalidated string conventions.
- Keep optionality accurate; do not claim a value is always present when failure or partial-result paths omit it.
- Avoid `Any` unless the boundary is intentionally extensible, such as metadata or provider-defined payloads.

### 5.4 Naming and Readability

- Use descriptive module, class, method, variable, and test names.
- Keep terminology aligned with the corresponding model and documentation.
- Prefer small cohesive methods and explicit control flow.
- Add comments and docstrings to explain responsibility, contract, or non-obvious reasoning; do not restate self-explanatory code.
- Preserve the repository's existing formatting and naming style in localized changes.

The repository currently does not declare a formatter, linter, type checker, or their configuration in `pyproject.toml`. Do not claim a specific tool's output as a required gate until it is adopted and configured.

### 5.5 Paths and Repository Safety

- Accept repository-relative paths at repository/workflow boundaries where the current contract requires them.
- Resolve and validate paths before reading or writing.
- Reject traversal outside the configured repository root.
- Restrict update operations to the artifact types and locations explicitly supported by the service.
- Preserve unrelated files and user changes.
- Prefer atomic or recoverable writes when modifying repository content.

### 5.6 Side Effects

Keep filesystem writes, network calls, model calls, process execution, and Git operations behind clear service boundaries. A method that performs a side effect should expose its success/failure contract and should not perform unrelated mutations.

## 6. Change-Implementation Standards

### 6.1 Minimal Change Principle

Make the smallest coherent change that solves the verified problem. Avoid unrelated cleanup, broad renaming, dependency upgrades, speculative extensibility, or refactoring during a focused fix.

Minimal does not mean incomplete. Update every directly affected producer, consumer, interface, test, template, configuration item, and document required to keep the change internally consistent.

### 6.2 Preserve Existing Behavior

Identify the behavior that must remain stable and protect it with existing or new regression tests. Do not change public contracts incidentally. When a contract must change, update callers and document compatibility consequences explicitly.

### 6.3 Diagnostic Changes

Temporary diagnostics must:

- answer a specific debugging question;
- be placed at a verified failure boundary;
- follow existing logging conventions;
- avoid secrets and excessive payloads; and
- include a removal or permanent-adoption decision.

Remove temporary diagnostics after resolution unless they provide justified ongoing operational value.

### 6.4 Structured Fault Isolation

Debug from evidence:

1. define expected and observed behavior;
2. identify a known-good state;
3. locate the first failing boundary;
4. inspect relevant inputs, state transitions, and outputs;
5. test the smallest plausible cause; and
6. verify the correction at the failing boundary and through affected integrations.

For workflows, trace lifecycle state and review/persistence boundaries. For UIs, trace route, service, view model, template, and stylesheet behavior together. For external providers, separate deterministic contract tests from live-service behavior.

### 6.5 No Silent Failure

Do not discard errors or warnings without a defined reason. Follow the boundary's implemented contract:

- return structured result errors where that service defines them;
- convert expected provider or validator failures as designed;
- raise an appropriate exception for invalid construction or unsupported calls; and
- translate lower-level failures into clear user-facing messages at the UI boundary.

Never expose secrets or unnecessary technical details in user-facing errors.

## 7. Configuration, Secrets, and Security

### 7.1 Runtime Configuration

Externalize values that vary by environment. `ProjectSettings` reads process environment variables at import time and applies source defaults when variables are absent.

Shell exports and Conda environment variables do not form separate precedence layers inside Project0; both supply the process environment. The value visible to the launched process wins according to the shell/Conda environment setup.

### 7.2 Secrets

Secrets and credentials must not be:

- committed to Git;
- embedded in production source or documentation;
- embedded as real values in tests or fixtures;
- logged;
- rendered in user interfaces; or
- included in exceptions, diffs, or generated artifacts intended for sharing.

Use environment variables for supported local credentials. Tests must use clearly non-sensitive dummy values and must not contact live services unless the test is explicitly classified as live integration validation.

### 7.3 External Content and Providers

Treat repository files, uploaded content, remote metadata, model output, and provider responses as untrusted input at their boundaries. Validate shape, type, required fields, size, paths, and supported operations before use. Preserve evidence provenance where research or documentation claims depend on external material.

### 7.4 Logging

- Use module-level loggers obtained with `logging.getLogger(__name__)`.
- Configure logging at executable composition boundaries.
- Select an appropriate level: debug for diagnostic detail, info for lifecycle milestones, warning for degraded but continuing behavior, and error/exception for failures.
- Avoid duplicate logging of the same exception at multiple layers unless each message adds distinct context.
- Never log API keys, credentials, complete sensitive inputs, or unnecessary model/provider payloads.

## 8. Testing Standards

### 8.1 Test Every Material Change

Production changes require tests at the lowest effective layer and at additional boundaries where integration or user-visible behavior could regress.

- Unit tests verify one component or contract in isolation.
- Integration tests verify collaboration between production components.
- Acceptance tests verify behavior through the intended external boundary, including browser UI behavior where applicable.

Agent-specific behavior belongs in the corresponding agent test suite; shared service behavior belongs in platform tests. One does not replace the other.

### 8.2 Determinism and Isolation

- Keep the regression suite independent of live networks, external AI services, and mutable external state whenever practical.
- Use injected stubs with contract-correct deterministic outputs.
- Keep tests isolated from each other and from the developer's real repository content or credentials.
- Use temporary directories and explicit fixtures for filesystem behavior.
- Do not use arbitrary sleep delays as synchronization or acceptance criteria.

Live-provider checks must be clearly separated from deterministic regression testing.

### 8.3 Test Behavior, Not Incidental Implementation

Assert observable results, state, side effects, error contracts, and user-visible output. Avoid tests coupled to private implementation details unless those details are themselves safety-critical invariants.

Use focused names such as `test_<expected_behavior>`. Preserve stable scenario identifiers where the test plan maps one behavior across integration and UI layers.

### 8.4 Regression Gate

Before considering a repository-wide change validated:

- run the focused tests for the changed behavior;
- run affected integration and acceptance suites;
- run `python -m pytest` when the environment supports the complete suite;
- run documentation validation when documentation changed; and
- distinguish tests actually executed from tests merely inspected.

Do not claim a pass count for a different commit or source state. Record skips, unavailable tools, environment limitations, and known source defects with the result.

See [Testing Guide](Testing_Guide.md) and the root `TEST_COMMANDS.md` for executable commands.

## 9. Documentation Standards

### 9.1 Documentation Is Part of the Change

Update affected documentation with the implementation. Documentation must distinguish:

- implemented behavior;
- project conventions;
- historical evidence;
- known limitations; and
- planned or possible future work.

Do not present planned behavior as implemented or preserve stale claims for narrative continuity.

### 9.2 Single Purpose and Authoritative Location

Each document should have one clear purpose. Define shared behavior once in the appropriate platform or project document and reference it from agent-specific documents rather than duplicating it. Markdown under `docs/` is the authoritative narrative format; generated site output is not source documentation.

### 9.3 Source-Grounded Claims

Every implementation claim should be supportable by current source, tests, configuration, or repository state. Use exact names and values where they form a contract. If a feature is incomplete or inconsistent, document the current behavior and limitation rather than smoothing over the discrepancy.

### 9.4 Validation

For documentation changes, inspect links and Markdown structure and run the applicable repository validators. Use `mkdocs build --strict` when MkDocs is available, and run source-compilation checks separately when the change affects Python. A tool that could not run must be reported as not run, not passed.

Follow [Documentation Standards](Documentation_Standards.md) for document organization, ownership, headers, diagrams, and cross-document consistency.

## 10. Human and AI Collaboration

### 10.1 Bounded Tasks

Provide AI tools with the target, authority, requested outcome, allowed scope, relevant dependencies, and validation expectation. Prefer bounded tasks that can be independently reviewed.

### 10.2 Reviewable Deliverables

AI-generated changes must be reviewable as ordinary engineering work. Provide complete replacement files or a clear diff as requested, identify validations performed, and do not commit, push, deploy, or mutate external systems unless the user explicitly authorizes that action.

### 10.3 No Invented Completion

Do not claim that code compiles, tests pass, documentation builds, a provider is reachable, or a change was persisted unless that action was actually completed against the stated source. Separate source inspection from execution evidence.

### 10.4 Preserve User Work

Assume existing uncommitted changes belong to the user. Do not overwrite, discard, reset, or reformat unrelated work. If the requested change overlaps ambiguous local modifications, stop and resolve the conflict with the user.

## 11. Git and Review Standards

- Inspect `git status --short` and relevant diffs before staging.
- Stage specific intended files; avoid broad staging when unrelated changes may exist.
- Use a concise commit message describing the completed behavior or documentation change.
- Keep production changes, their tests, and directly affected documentation together when practical.
- Do not rewrite shared history or use destructive recovery commands without explicit authorization.
- Do not commit generated output, credentials, local environments, caches, or unrelated files.
- Review the final diff for accidental scope growth, secret exposure, debug code, and stale documentation before committing.

## 12. Definition of Done

A change is complete when, as applicable:

- the requested behavior is implemented at the correct ownership boundary;
- public interfaces and shared models remain coherent;
- affected tests are added or updated;
- focused and regression validation has been executed or limitations are reported;
- affected documentation is current and source-grounded;
- error, logging, security, and path-safety behavior has been considered;
- the final diff contains only intended changes; and
- no result, pass count, external action, or deployment is claimed without evidence.

## 13. Current Tooling Boundaries and Future Improvements

The pinned repository declares pytest but does not configure a formatter, linter, type checker, coverage tool, security scanner, or continuous-integration workflow in `pyproject.toml`. Browser acceptance dependencies are also not declared in the test extra.

Possible future improvements include:

- automated formatting and linting;
- static type checking;
- coverage reporting;
- dependency and security scanning;
- continuous-integration regression and documentation builds;
- dependency locking; and
- documented performance and benchmark standards.

These items are future work until they are implemented and adopted by the repository.

## 14. Summary

Project0 engineering requires source-grounded decisions, explicit interfaces, clear ownership, minimal coherent changes, deterministic testing, synchronized documentation, safe configuration, and evidence-based completion claims. The standard is not merely to make a change work in isolation, but to keep the platform understandable and reliable as it evolves.
