# Agent Skills Design

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-13  
**Status:** Implemented foundation with two repository-local skills; selective workflow integration  
**Source Baseline:** `main` at `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`

## Executive Summary

Project0 supports repository-local, version-controlled instruction packages
that are discovered and validated by a shared registry, explicitly activated by
a workflow, and attached to reasoning requests. Two local skill definitions now
exist: `strict-documentation-editor` and
`evidence-grounded-research-analyst`. Runtime integration is intentionally
selective rather than agent-wide: source-grounded Documentation Workflow
proposal generation activates `strict-documentation-editor`, while the
Research Workflow does not activate `evidence-grounded-research-analyst`.
Research Agent evaluation showed that broad skill activation degraded relevance
scoring and contributed to Research Direction warnings, so the Research
integration was reverted. Skills guide the model; deterministic Python controls
retain authority over scope, evidence, validation, review, and repository
changes.

## Purpose and Scope

This document defines the implemented skill format, registry, reasoning
integration, workflow activation, and enforcement boundary. It does not define
a marketplace, dependency manager, execution runtime, remote registry, or
automatic selection framework.

The design favors repository-local reviewability, metadata-only discovery,
on-demand instruction loading, explicit and selective workflow activation,
separation of registry/workflow/prompt responsibilities, and fail-closed
loading when a configured workflow requires a skill.

## Component Design

### Repository format

Each immediate child directory beneath `skills/` may contain one `SKILL.md`:

```text
skills/
├── evidence-grounded-research-analyst/
│   └── SKILL.md
└── strict-documentation-editor/
    └── SKILL.md
```

A skill file begins with YAML frontmatter and continues with Markdown
instructions. Required fields are a non-empty lowercase kebab-case `name` and a
non-empty `description`; the declared name must match its directory. Additional
frontmatter is retained as metadata. Frontmatter must start on line one, close
with `---`, and parse as a YAML mapping.

### Models and registry

`SkillMetadata` contains `name`, `description`, `skill_path`, and mutable
`metadata`. `SkillDefinition` adds the instruction body. Both dataclasses are
frozen and slotted, but dictionary immutability remains shallow.

`SkillRegistry(skills_root)` resolves its root at construction. `discover()`
returns an empty tuple for a missing root, rejects a non-directory root, scans
immediate child directories in name order, ignores children without `SKILL.md`,
validates each discovered definition, and returns metadata without loading
instructions. Malformed discovered skills raise errors.

`load(name)` trims and validates the name, resolves and contains the path,
requires the file, validates the complete definition, and returns instructions.
Invalid names, path escapes, missing files, malformed YAML, missing fields, and
name mismatches raise `ValueError`. The registry neither downloads nor executes
skills, modifies files, persists registration, nor selects a skill.

### Local skills

`strict-documentation-editor` classifies itself as documentation/local. Its
instructions require minimal, source-grounded, precisely placed Markdown
updates that preserve unrelated content and avoid invented implementation
details.

`evidence-grounded-research-analyst` classifies itself as research/local. Its
instructions require evidence-grounded research analysis that preserves source
identity and provenance, distinguishes discovery metadata from substantive
evidence, avoids unsupported findings and comparisons, represents uncertainty
when evidence is insufficient, and does not override deterministic Research
Agent workflow controls.

## Interactions and Contracts

`PlatformDispatcher` constructs `SkillRegistry(repository_root / "skills")`
and supplies it to the Documentation Workflow factory. The Research Workflow
does not receive the registry, so the
`evidence-grounded-research-analyst` definition is intentionally not activated.
Skill availability therefore does not imply automatic activation by every
agent or workflow.

`ReasoningRequest.skills` is a tuple of loaded definitions. For each active
skill, `PromptBuilder` appends a labeled instruction block and records its name
in provider metadata as `skill_names`. With no skills, normal prompting remains
unchanged and `skill_names` is empty.

For source-grounded Documentation requests, gap analysis runs first without a
skill and cannot propose edits. When gaps exist, proposal generation receives
those gaps and the strict skill. No-gap processing stops without proposals. A
required-skill load failure fails the source-grounded workflow. Ordinary
Documentation requests do not activate the skill.

## Configuration and Failure Behavior

Documentation activation depends on non-empty
`DocumentationWorkflowRequest.source_paths` and an available registry. Registry
discovery/loading failures propagate as validation errors; required skill
failure does not silently downgrade the workflow. No Research Workflow skill
activation path is implemented; the Research skill remains available in the
repository without being part of the active Research Workflow.

Skill text has no direct authority to read, write, execute, approve, or publish.
Deterministic workflow logic continues to enforce requested target paths,
read-only source evidence, supported operations, established gaps, concrete
Markdown, source-derived Python meaning and canonical declarations, section and
artifact placement, semantic alignment, stale content, validation, human
review, and controlled application.

## Constraints and Verification

Current exclusions include external discovery/installation/trust, dependencies,
skill code execution, persistent registry state outside Git, semantic automatic
selection, automatic availability in every workflow, Research Workflow skill
activation, nested discovery, version resolution, migration, and runtime user
management. Skills are applied only where controlled evaluation shows that the
additional instruction layer improves the target workflow.

Substantive coverage exists in `test_skill_registry.py`,
`test_prompt_builder.py`, and `test_documentation_workflow.py` for discovery,
loading, validation, prompt propagation, conditional activation, two-stage
reasoning, fail-closed behavior, target/evidence controls, placement,
validation, review, and completion. `test_skill_models.py` is effectively empty;
the checked-in source, not a dedicated model test, supports frozen/slotted model
behavior.

Future work may revisit stage-specific Research skill activation only where
controlled evaluation demonstrates value without degrading candidate selection,
relevance scoring, or downstream synthesis. Other future work may add provenance
and trust policy, controlled installation and updates, dependency/capability
metadata, compatibility rules, broader selective workflow integration, and
auditable selection while preserving the separation among discovery, activation,
prompt rendering, deterministic enforcement, and execution authority.
