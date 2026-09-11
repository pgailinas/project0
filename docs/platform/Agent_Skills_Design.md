# Agent Skills Design

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-09-11  
**Status:** Implemented foundation with one workflow-specific local skill  
**Source Baseline:** `main` at `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`

## Executive Summary

Project0 supports repository-local, version-controlled instruction packages
that are discovered and validated by a shared registry, explicitly activated by
a workflow, and attached to reasoning requests. The current implementation is
deliberately narrow: only source-grounded Documentation Workflow proposal
generation activates the `strict-documentation-editor` skill. Skills guide the
model; deterministic Python controls retain authority over scope, evidence,
validation, review, and repository changes.

## Purpose and Scope

This document defines the implemented skill format, registry, reasoning
integration, workflow activation, and enforcement boundary. It does not define
a marketplace, dependency manager, execution runtime, remote registry, or
automatic selection framework.

The design favors repository-local reviewability, metadata-only discovery,
on-demand instruction loading, explicit workflow activation, separation of
registry/workflow/prompt responsibilities, and fail-closed loading when a
configured workflow requires a skill.

## Component Design

### Repository format

Each immediate child directory beneath `skills/` may contain one `SKILL.md`:

```text
skills/
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

### Initial skill

`strict-documentation-editor` is the only current local skill. Its metadata
classifies it as documentation/local, and its instructions require minimal,
source-grounded, precisely placed Markdown updates that preserve unrelated
content and avoid invented implementation details.

## Interactions and Contracts

`PlatformDispatcher` constructs `SkillRegistry(repository_root / "skills")`
and supplies it to the Documentation Workflow factory. The Research Workflow
does not receive it.

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

Activation depends on non-empty `DocumentationWorkflowRequest.source_paths` and
an available registry. Registry discovery/loading failures propagate as
validation errors; required skill failure does not silently downgrade the
workflow.

Skill text has no direct authority to read, write, execute, approve, or publish.
Deterministic workflow logic continues to enforce requested target paths,
read-only source evidence, supported operations, established gaps, concrete
Markdown, source-derived Python meaning and canonical declarations, section and
artifact placement, semantic alignment, stale content, validation, human
review, and controlled application.

## Constraints and Verification

Current exclusions include external discovery/installation/trust, dependencies,
skill code execution, persistent registry state outside Git, semantic automatic
selection, automatic availability in every workflow, nested discovery, version
resolution, migration, and runtime user management.

Substantive coverage exists in `test_skill_registry.py`,
`test_prompt_builder.py`, and `test_documentation_workflow.py` for discovery,
loading, validation, prompt propagation, conditional activation, two-stage
reasoning, fail-closed behavior, target/evidence controls, placement,
validation, review, and completion. `test_skill_models.py` is effectively empty;
the checked-in source, not a dedicated model test, supports frozen/slotted model
behavior. This design record does not claim that those tests were executed.

Future work may add provenance and trust policy, controlled installation and
updates, dependency/capability metadata, compatibility rules, broader workflow
integration, and auditable selection while preserving the separation among
discovery, activation, prompt rendering, deterministic enforcement, and
execution authority.
