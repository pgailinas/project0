# Agent Skills Design

**Status:** Implemented foundation with one workflow-specific local skill  
**Version:** 0.3  
**Last updated:** 2026-09-11  
**Source baseline:** `main` at `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`

## 1. Purpose

Project0 supports repository-local agent skills: versioned instruction packages that can be discovered, validated, loaded, and attached to reasoning requests. A skill specializes model behavior without hard-coding all behavioral guidance into workflow or prompt-builder code.

The current implementation provides:

- a directory-based skill format;
- validated metadata discovery and on-demand instruction loading;
- shared skill models;
- a repository-scoped registry assembled by the platform dispatcher;
- reasoning-request and prompt-builder integration; and
- one local skill used by source-grounded Documentation Workflow requests.

The implementation is deliberately narrow. It is not yet a general skill marketplace, dependency system, execution runtime, or automatic skill-selection framework.

## 2. Design Principles

### Repository-local and version-controlled

Skills live in the repository and evolve with the code that consumes them. This keeps behavior reviewable and ties skill changes to the same change-control process as application code.

### Metadata-first discovery

Discovery reads and validates frontmatter but does not load instruction bodies. Full instructions are loaded only when a caller selects a skill by name.

### Explicit activation

The registry does not choose skills. A workflow explicitly loads a named skill and places the resulting definition on a reasoning request.

### Separation of responsibilities

- Skill files define reusable model-facing guidance.
- `SkillRegistry` discovers and validates local definitions.
- Workflows decide when a skill applies.
- `PromptBuilder` renders active instructions into the provider request.
- Deterministic workflow code continues to enforce paths, proposal shape, source fidelity, validation, and review boundaries.

### Safe failure

Malformed discovered skills raise validation errors. In the configured source-grounded Documentation Workflow, failure to load the required strict skill fails the workflow closed instead of silently continuing without it.

## 3. Repository Structure

Each skill occupies one immediate child directory under the repository's `skills/` root:

```text
skills/
└── strict-documentation-editor/
    └── SKILL.md
```

The current registry scans only immediate child directories. A directory without `SKILL.md` is ignored.

## 4. Skill File Format

A `SKILL.md` file contains YAML frontmatter followed by Markdown instructions:

```markdown
---
name: strict-documentation-editor
description: Performs minimal source-grounded updates to existing controlled Markdown documentation while preserving unrelated content and exact repository locations.
metadata:
  category: documentation
  project0-phase: local
---

# Strict Documentation Editor

Instruction body...
```

Required frontmatter fields:

- `name`: a non-empty lowercase kebab-case identifier matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`;
- `description`: a non-empty string.

The declared `name` must equal the containing directory name. Additional frontmatter is preserved as metadata. Frontmatter must begin on the first line, end with a closing `---`, and parse to a YAML mapping.

## 5. Shared Models

`src/project0/models/skill_models.py` defines:

### `SkillMetadata`

- `name: str`
- `description: str`
- `skill_path: Path`
- `metadata: dict[str, object]`

### `SkillDefinition`

- all metadata fields above;
- `instructions: str`

Both dataclasses use `frozen=True` and `slots=True`. This prevents field reassignment, but immutability is shallow: the `metadata` value is a mutable dictionary.

## 6. Skill Registry

`src/project0/skills/skill_registry.py` provides `SkillRegistry`.

### Construction

`SkillRegistry(skills_root)` resolves the supplied root path immediately.

### Discovery

`discover()`:

1. returns an empty tuple when the skills root does not exist;
2. raises `ValueError` when the root exists but is not a directory;
3. examines immediate child directories in name-sorted order;
4. ignores children without `SKILL.md`;
5. validates frontmatter, required fields, name syntax, and directory-name agreement; and
6. returns `SkillMetadata` objects without loading instruction bodies.

If a discovered `SKILL.md` is invalid, its validation error propagates. Discovery does not silently skip malformed skill files.

### Loading

`load(name)`:

1. strips surrounding whitespace;
2. validates the name against the skill-name pattern;
3. resolves `<skills_root>/<name>/SKILL.md`;
4. verifies the resolved path remains within the configured skills root;
5. requires the file to exist;
6. parses and validates the complete file; and
7. returns a `SkillDefinition` containing the instruction body.

Invalid names, path-escape attempts, missing skills, malformed YAML, missing fields, and name mismatches raise `ValueError`.

### Registry boundary

The registry reads repository-local Markdown files. It does not download skills, execute code, interpret instructions, modify skill files, persist registration state, or select a skill for a request.

## 7. Platform Integration

`PlatformDispatcher` constructs the shared registry from:

```python
SkillRegistry(repository_root / "skills")
```

The dispatcher retains the registry and supplies it to the Documentation Workflow factory. The Research Workflow does not currently receive the registry.

This means repository-local skill infrastructure is platform-owned, while activation remains workflow-specific.

## 8. Reasoning Integration

`ReasoningRequest` exposes:

```python
skills: tuple[SkillDefinition, ...] = ()
```

When active skills are present, `PromptBuilder`:

- appends each instruction body to the system instructions under a labeled section of the form `=== ACTIVE AGENT SKILL: <name> ===`; and
- records the active names in provider-request metadata as `skill_names`.

With no active skills, the normal prompt path is preserved and `skill_names` is an empty tuple.

## 9. Documentation Workflow Integration

The first local skill is `strict-documentation-editor`.

### Activation rule

The Documentation Workflow loads this skill only when `DocumentationWorkflowRequest.source_paths` is non-empty and a registry is configured. Ordinary documentation requests do not load it.

For a source-grounded request, processing has two reasoning stages:

1. **Gap analysis** compares the controlled documentation with authoritative source context. This request uses `workflow_type="documentation_gap_analysis"`, carries no active skills, and must not propose edits.
2. **Proposal generation** runs only when gaps were established. It uses `workflow_type="documentation_update"`, receives the established gaps in context, and carries the strict documentation skill.

If gap analysis finds no gaps, the workflow stops before edit generation and returns a review-required result with no proposals. If the required skill cannot be loaded, the source-grounded workflow returns a failed result.

The strict skill owns persistent model-facing editing policy: make minimal source-grounded changes, preserve unrelated content and existing structure, use exact repository locations, emit concrete Markdown rather than planning language, and avoid inventing implementation details.

## 10. Deterministic Enforcement Boundary

Skill instructions guide the model; they are not the enforcement mechanism. The Documentation Workflow and prompt schema retain deterministic controls, including:

- limiting proposed document paths to requested targets when targets are supplied;
- treating authoritative source paths as read-only evidence rather than edit targets;
- accepting supported documentation operations and building typed proposals;
- rejecting source-grounded meta-instructions or planning recommendations instead of concrete documentation;
- requiring source-grounded proposals to correspond to established gaps;
- requiring an explicit documentation meaning for source-derived Python content and rejecting rationale-like meanings;
- preventing new Python fences when the target document does not establish that form;
- canonicalizing uniquely matched Python declarations to authoritative source text and rejecting ungrounded or ambiguous declarations;
- resolving proposed sections and artifact locations before review;
- checking semantic alignment between a proposed change and its target section, with conservative recovery only when a unique suitable section can be resolved;
- preserving section structure for snippet edits and distinguishing them from complete section replacements;
- validating proposal paths before review; and
- retaining human review and repository-update stages outside the reasoning model.

These controls remain necessary even when the strict skill is active.

## 11. Initial Local Skill

`skills/strict-documentation-editor/SKILL.md` is the only repository-local skill currently present. Its frontmatter declares:

- name: `strict-documentation-editor`;
- category: `documentation`;
- project phase: `local`.

Its instructions are scoped to controlled Markdown maintenance backed by repository source. They emphasize minimal edits, source fidelity, format preservation, precise placement, and concrete publishable content.

## 12. Validation and Test Evidence

The source tree contains substantive automated coverage in:

- `tests/unit/skills/test_skill_registry.py` for discovery, ordering, metadata-only reads, loading, invalid format, name validation, containment, missing roots, and malformed discovered skills;
- `tests/unit/reasoning/test_prompt_builder.py` for active-skill rendering, `skill_names` metadata, no-skill behavior, gap-analysis contracts, target-path/schema restrictions, and source-grounded response guidance; and
- `tests/unit/workflow/test_documentation_workflow.py` for conditional activation, fail-closed loading, two-stage source-grounded reasoning, no-gap termination, target scoping, meta-instruction rejection, source declaration handling, semantic section alignment and recovery, artifact location, validation, review, and completion behavior.

`tests/unit/models/test_skill_models.py` is currently effectively empty and does not provide substantive model-test coverage. The frozen/slotted model behavior is therefore represented by implementation, not by dedicated model tests in this baseline.

This document describes the checked-in design and test coverage; it does not claim that the test suite was executed as part of this document merge.

## 13. State, Trust, and Execution Boundaries

The current design intentionally excludes:

- external discovery, download, installation, or trust verification;
- dependency declaration or dependency resolution;
- a skill-specific code execution environment;
- persistent registry state or skill version history outside Git;
- dynamic skill selection based on request semantics;
- automatic skill availability in every workflow or agent; and
- nested skill discovery below immediate child directories.

A loaded skill is text injected into a reasoning request. It has no direct authority to read, write, execute, approve, or publish anything.

## 14. Future Expansion

Likely extensions include externally sourced skills with provenance and trust policy, controlled installation and updates, dependency metadata, capability declarations, version compatibility, broader workflow integration, and auditable selection policy. Those features should build on the current separation between discovery, activation, prompt rendering, deterministic enforcement, and execution authority.

## 15. Summary

Project0 now has a small but complete local-skill foundation. Skills are validated repository artifacts; the platform owns a shared registry; workflows explicitly activate them; and the prompt builder injects their instructions into reasoning requests. Today, only source-grounded Documentation Workflow proposal generation uses a skill. Deterministic workflow controls remain the authority for safety, scope, validation, and review.
