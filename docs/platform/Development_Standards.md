# Development Standards

**Version:** 0.7  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## Purpose and Authority

This document defines engineering standards for human- and AI-assisted design,
implementation, testing, documentation, and review across Project0. It governs
the shared platform, Dashboard, agents, tests, and repository documentation.
Current source, tests, configuration, templates, and documentation establish
implementation context. When implementation differs from a standard, record
the discrepancy rather than presenting the convention as implemented behavior.

The goals are maintainable architecture, controlled complexity, clear
decisions, safe minimal changes, effective collaboration, deterministic
validation, and reliable evolution.

## Reference Content

### Engineering and evidence principles

- Reuse proven solutions; introduce novelty only for a demonstrated, measurable
  need.
- Every component must have a clear problem, benefit, integration cost,
  validation plan, and maintenance owner.
- Select technology on requirements, maturity, maintainability, stability,
  support, integration, licensing, security, and operations.
- Design before implementation at a depth proportional to the change, covering
  ownership, interfaces, flow, dependencies, errors, state, security, and tests.
- Maintain shared terminology and prefer explicit typed dependencies, bounded
  workflows, and readable implementations over speculative abstraction.

Inspect the current target branch or designated baseline before changing code.
Source, tests, configuration, templates, and dependencies are authoritative for
implemented behavior; stale prose is not. When exact supplied files are the
baseline, preserve their scope and unrelated content while verifying required
dependencies. Strict mode constrains edit scope but does not make an isolated
file globally authoritative.

Before a change, verify names, imports, boundaries, parameters, return/status
contracts, UI layers, configuration defaults, path behavior, and relevant
tests. State uncertainty instead of inventing behavior.

### Architecture and code

Each component should own one coherent responsibility. Keep shared platform
services separate from agent-specific behavior. Define meaningful substitutable
boundaries using typed `Protocol` interfaces with explicit input, output, state,
failure, and side-effect contracts. Inject collaborators; assemble production
dependencies at dispatcher/application composition boundaries.

Use typed shared models, frozen/slotted dataclasses and tuples where stable,
`StrEnum` for contract values, accurate optionality, and `Any` only at
intentionally extensible boundaries. Do not introduce a generic envelope unless
multiple implemented consumers require it. Preserve exact enum strings and
field meanings.

Do not assume every workflow uses the generic engine. Generic context,
Documentation, and Research workflows have separate orchestration/state/result
contracts. Make identifiers, status, completed/failed stages, warnings/errors,
next action, and persistence boundaries observable. Identify the first useful
failure boundary.

Production code must remain under `src/project0/`, support Python 3.12+, use
absolute `project0...` cross-package imports, run as installed modules with
`python -m`, and declare dependencies in `pyproject.toml`. Python files must use
the exact Project0 header defined by [Documentation
Standards](Documentation_Standards.md).

Type public APIs; use descriptive, consistent names; prefer cohesive methods
and explicit flow; document responsibility or non-obvious reasoning; and
preserve local style. No formatter, linter, type checker, or corresponding gate
is currently configured.

Paths must be repository-relative where the contract requires, resolved and
contained before use, restricted to supported artifact types/locations, and
handled without disturbing unrelated user work. Prefer atomic or recoverable
writes. Isolate filesystem, network, model, process, and Git side effects behind
clear contracts.

### Change and fault isolation

Make the smallest coherent change that solves the verified problem, while
updating every directly affected producer, consumer, interface, test, template,
configuration item, and document. Protect stable behavior with regression tests;
when a public contract must change, update callers and document compatibility.

Temporary diagnostics must answer a specific question at a verified boundary,
follow logging conventions, avoid secrets/excessive payloads, and have a
removal/adoption decision. Debug by defining expected/observed behavior,
identifying a known-good state and first failing boundary, inspecting inputs and
state transitions, testing the smallest cause, and verifying affected
integrations. Trace all UI layers together and separate deterministic provider
contracts from live-service behavior.

Do not silently discard warnings or errors. Return structured errors where
defined, convert expected failures as designed, raise suitable exceptions for
invalid construction/unsupported calls, and translate failures safely at the
UI boundary.

### Configuration, security, and logging

Externalize environment-varying values. `ProjectSettings` reads the process
environment at import; shell and Conda variables simply contribute to that
environment. Never commit, embed, log, render, or share real secrets. Tests use
non-sensitive dummy values and contact live services only when explicitly
classified as live integration.

Treat repository/uploaded/remote/model/provider content as untrusted. Validate
shape, type, required fields, size, paths, operations, and evidence provenance.
Use module loggers; configure logging at executable boundaries; choose levels by
purpose; avoid duplicate exception logging; and exclude secrets and unnecessary
payloads.

### Testing and documentation

Every material production change requires tests at the lowest effective layer
and at integration or external boundaries that may regress. Unit tests isolate
contracts, integration tests assemble production components, and acceptance
tests exercise intended external behavior. Shared and agent-specific ownership
remain separate.

Regression tests should avoid live networks/models/state, use contract-correct
stubs, isolate filesystem/credentials, and avoid arbitrary sleeps. Assert
observable behavior rather than incidental internals unless safety-critical.
Use focused test names and stable scenario identifiers where applicable.

Before claiming repository-wide validation, run focused tests, affected
integration/acceptance suites, `python -m pytest`, and applicable documentation
validation. Record the exact commit, skips, unavailable tools, environment
limits, and source defects; do not reuse a count from another state. See the
[Testing Guide](Testing_Guide.md) and `TEST_COMMANDS.md`.

Documentation is part of the change and must distinguish implemented behavior,
convention, history, limitations, and future work. Give each document one
purpose, define shared behavior once, ground claims in evidence, validate links
and Markdown, and run `mkdocs build --strict` when available. Follow
[Documentation Standards](Documentation_Standards.md).

### Collaboration, Git, and completion

AI tasks must specify target, authority, outcome, scope, dependencies, and
validation. Deliverables must be ordinarily reviewable. Do not commit, push,
deploy, or mutate external systems without explicit authority; do not claim
compilation, tests, builds, provider access, or persistence without execution.
Preserve all unrelated user work and resolve overlapping ambiguity before
editing.

Inspect status/diffs, stage specific intended files, use concise messages, keep
directly related code/tests/docs together when practical, avoid destructive
history changes, exclude generated/local/secret material, and review for scope,
secrets, diagnostics, and stale documentation.

A change is done when applicable behavior is correctly owned; contracts remain
coherent; tests and documentation are updated; validation was executed or its
limits reported; safety/error/logging/security are considered; the diff is
scoped; and every result or external-action claim has evidence.

## Constraints and Notes

The repository currently declares pytest but no formatter, linter, type checker,
coverage tool, security scanner, CI workflow, dependency lock, performance
standard, or browser dependencies in the test extra. These remain possible
future improvements until implemented and adopted; they are not current gates.
