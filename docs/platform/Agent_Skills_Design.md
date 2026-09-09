# Project0 Agent Skills Design

**Version:** 0.1  
**Owner:** Project0  
**Last Updated:** 2026-09-09

---

## 1. Purpose

### Objective

Define the implemented Project0 platform design for repository-local
Agent Skills.

### Scope

Describe the Agent Skill repository structure, shared models, registry,
loading behavior, reasoning integration, current Documentation Agent
integration, deterministic enforcement boundaries, and validation
behavior supported by the current implementation.

External skill discovery, download, installation, trust validation, and
approval are outside the current implementation scope.

---

## 2. Design Principles

* Agent Skills are repository-local Project0 capabilities.
* Skill definitions are stored separately from Python implementation.
* Skill discovery and loading are deterministic.
* Full skill instructions are loaded only when a skill is selected.
* Shared immutable models represent discovered and loaded skills.
* Skills guide AI reasoning but do not replace deterministic workflow
  validation or safety enforcement.
* Existing workflows preserve no-skill behavior when no skill is active.

---

## 3. Repository Structure

Repository-local skill definitions use a directory-per-skill structure:

``` text
skills/
└── <skill-name>/
    └── SKILL.md
```

The platform implementation is stored under:

``` text
src/project0/
├── models/
│   └── skill_models.py
└── skills/
    └── skill_registry.py
```

Skill unit coverage is stored under `tests/unit/skills/`, with shared
skill model tests under `tests/unit/models/`.

---

## 4. Skill Definition Format

Each repository-local skill is defined by `SKILL.md`.

The current Skill Registry requires YAML frontmatter containing:

* `name`
* `description`

Additional frontmatter values are preserved as skill metadata.

The frontmatter `name` must match the skill directory name and use
lowercase letters, numbers, and hyphens.

Markdown following the frontmatter is treated as the full skill
instruction content.

---

## 5. Shared Skill Models

### Skill Metadata

`SkillMetadata` represents metadata discovered from a local skill
without requiring full instruction loading.

Fields:

* `name`
* `description`
* `skill_path`
* `metadata`

### Skill Definition

`SkillDefinition` represents a fully loaded Agent Skill.

Fields:

* `name`
* `description`
* `skill_path`
* `instructions`
* `metadata`

Both models are immutable dataclasses.

---

## 6. Skill Registry

The `SkillRegistry` provides deterministic repository-local skill
discovery and loading.

### Discovery

`discover()`:

* Returns an empty result when the configured skills directory does not
  exist.
* Enumerates skill directories in deterministic name order.
* Recognizes directories containing `SKILL.md`.
* Validates required frontmatter.
* Returns `SkillMetadata` without loading full instructions.

### Loading

`load(name)`:

* Validates the requested stable skill name.
* Resolves the skill within the configured skills root.
* Rejects paths outside the configured skills root.
* Requires the skill file to exist.
* Validates frontmatter and directory/name agreement.
* Returns a fully loaded `SkillDefinition`.

---

## 7. Platform Integration

The Platform Dispatcher creates one repository-local Skill Registry
using:

``` text
<repository-root>/skills
```

The configured registry is exposed by the Platform Dispatcher and is
provided to the Documentation Workflow during default platform
assembly.

---

## 8. Reasoning Integration

`ReasoningRequest` supports:

``` text
skills: tuple[SkillDefinition, ...]
```

When active skills are present, Prompt Builder:

* Appends each active skill's instructions to the provider system
  instructions.
* Labels the appended section with the active skill name.
* Records active skill names in provider request metadata.

When no skills are active, the normal reasoning prompt behavior is
preserved.

---

## 9. Documentation Agent Integration

The current implemented skill integration is limited to source-grounded
Documentation Agent requests.

When a Documentation Workflow request contains Ground Truth Source
Paths:

1. The source-grounded context is built from only the requested target
   documentation and authoritative source paths.
2. The Documentation Workflow loads
   `strict-documentation-editor` from the configured Skill Registry.
3. The loaded skill is attached to the Reasoning Request.
4. Prompt Builder appends the skill instructions to the provider system
   instructions.
5. The Reasoning Service generates proposed documentation changes.
6. The Documentation Workflow applies deterministic proposal guards
   before any proposal reaches review.

Documentation requests without Ground Truth Source Paths do not load
the strict documentation skill.

---

## 10. Deterministic Enforcement Boundary

Agent Skill instructions guide model behavior. They are not treated as a
replacement for deterministic workflow enforcement.

For source-grounded Documentation Workflows, deterministic enforcement
includes:

* Restricting proposals to requested target paths.
* Rejecting unsupported documentation operations.
* Restricting changes to Markdown files within the repository.
* Rejecting meta-instruction content that describes what should be
  written instead of providing concrete Markdown.
* Requiring unambiguous artifact locations or exact target anchors.
* Rejecting ambiguous or missing anchors.
* Validating semantic alignment between proposed changes and target
  sections.
* Recovering to a section only when one unique semantic candidate is
  available.
* Preserving existing sections when a proposed replacement contains only
  a localized snippet.
* Verifying fenced Python function, async function, and class
  declarations against authoritative Python source declarations when
  authoritative Python source is available.
* Rejecting source-grounded Python declarations that do not exactly
  match an authoritative source declaration.

These checks remain workflow responsibilities even when a skill is
active.

---

## 11. Initial Local Skill

The initial repository-local skill is:

``` text
skills/strict-documentation-editor/SKILL.md
```

It is used by source-grounded Documentation Agent workflows to guide
minimal controlled Markdown updates while deterministic workflow guards
continue to enforce target scope, location safety, and source fidelity.

---

## 12. Validation

The implemented Agent Skills foundation includes automated coverage for:

* Skill metadata discovery.
* Deterministic discovery order.
* Full skill loading.
* Missing skills directory behavior.
* Unknown skill rejection.
* Skill path traversal rejection.
* Required YAML frontmatter.
* Required name and description values.
* Directory/name agreement.
* Source-grounded Documentation Workflow skill loading.
* Preservation of no-skill behavior for ordinary documentation
  requests.
* Fail-closed behavior when the strict documentation skill cannot be
  loaded.
* Source-grounded proposal safety and source-fidelity enforcement.

---

## 13. Current Scope and Future Expansion

The current implementation supports repository-local Agent Skills only.

Future expansion may evaluate external `SKILL.md` compatibility or
import. External skill use requires a separate trust-validation and
approval design before it can become part of the implemented platform.
