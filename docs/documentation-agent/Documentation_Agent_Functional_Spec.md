# Documentation Agent Functional Specification

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-11

## 1. Purpose and Scope

The Documentation Agent shall provide an AI-assisted, human-controlled workflow for synchronizing existing Markdown documentation with explicitly supplied repository evidence or repository documentation selected from a user request.

It shall generate reviewable proposals, apply only individually approved changes, validate affected paths at the implemented stages, and report a path-scoped Git diff. It is hosted in the Project0 Dashboard while workflow and repository behavior remain outside the shared Dashboard Framework.

The agent does not automatically derive requests or source-code impact from staged or unstaged Git changes. Evidence enters through explicit source paths or ordinary documentation-knowledge selection.

## 2. Functional Requirements

### Core behavior

The Documentation Agent shall:

- Treat supplied source paths as read-only authoritative evidence and existing target Markdown as controlled documentation.
- Use structured AI reasoning for interpretive work and deterministic services for path, operation, location, validation, application, and repository safety.
- Build context in source-grounded or ordinary mode.
- Perform two-stage gap analysis and proposal generation when source paths are supplied, or one documentation-update request otherwise.
- Generate concrete, localized, minimum-necessary proposals with rationales and focused differences.
- Accept only updates to permitted existing Markdown targets.
- Fail closed when source-grounded scope, content, semantics, or location is unsupported or ambiguous.
- Require one human decision per proposal and write only approved, non-stale changes.
- Run preliminary and final validation at their implemented boundaries.
- Return structured status, warnings, errors, counters, and an applied-path Git diff.

### Proposal enforcement

Every proposed change shall exactly match the target allowlist when one exists, use the `update` operation, remain inside the repository, have a lowercase-normalized `.md` suffix, resolve to an existing file, and retain the full original content snapshot. Unsupported create and delete operations shall be skipped with warnings.

Source-grounded content must be concrete Markdown, not writing instructions. A fenced Python declaration may be replaced by `documentation_meaning` only when the prose is concrete, nonempty, not rationale-like, and contains no fenced Python. A proposed function, asynchronous function, or class declaration must exactly match authoritative Python source when authoritative declarations exist; canonicalization requires exactly one match.

Location resolution shall prefer an exact section and then use rationale discovery. Ambiguous locations fail. Unresolved source-grounded locations require one exact unique anchor. Section content must have meaningful term overlap; recovery to an existing subsection requires a unique highest positive score. A replace operation that targets a section shall preserve its exact heading when the proposed content omits it. Insert edits use insert-after anchor behavior; replace and delete edit types use replace-anchor behavior, although the executable operation remains `update`. Before review, the workflow shall apply each resolved proposal in memory and skip it with an explicit warning when the resulting content is byte-for-byte identical to the original document.

### Validation and application

The default workflow uses Markdown, Link, and MkDocs validators; Documentation Consistency Validator is not in the default tuple. Preliminary validation checks current proposal paths before review and does not build a candidate tree. Failures retain proposals with failed status; warnings retain review state.

Final validation checks only successfully applied paths and is absent when nothing was applied. Its warnings or failures affect status but do not roll back completed writes. Unexpected validator exceptions become failed validator results while remaining validators continue.

Repository Update Service shall validate matching proposal/review IDs, require approval, resolve the existing Markdown target within the repository, reject stale snapshots, apply the selected unique location or anchor, write UTF-8 through a temporary file and atomic replacement, preserve an existing final newline, clean up temporary files when possible, and return applied, skipped, or failed status. Before a later same-file approval, Documentation Workflow may rebase the proposal only onto the latest successful write from that workflow. Anchor targets must remain valid, and line-range targets must be uniquely relocatable by unchanged exact content. Whole-file or overlapping combinations fail closed. The repository service shall still compare the rebased expected snapshot with current disk content so external edits are not accepted implicitly.

## 3. Inputs and Outputs

### Request inputs

- `user_request` is required and nonblank. UI and Platform Dispatcher independently reject blank input.
- `target_paths` are optional repository-relative paths forming an exact proposal allowlist. Without source paths, Knowledge Service may select relevant Markdown when targets are omitted. No implicit baseline list replaces them.
- `source_paths` are optional read-only authoritative repository paths. At least one activates two-stage source-grounded behavior; a usable target must still be established.
- `workflow_id` is optional; Platform Dispatcher generates a UUID when omitted. State and review operations require a nonblank ID.
- Browser source and target paths are newline-separated, trimmed, and stripped of blank lines; route parsing does not remove duplicates.

### Reasoning outputs

Stage 1 `documentation_gap_analysis` output shall contain summary, gaps, assumptions, and warnings. Each gap identifies its target document, optional section, description, source evidence, and optional confidence. Exact semantic duplicates are removed. For an HTTP endpoint return claim, analysis shall ground the contract in returned payload fields rather than docstring wording. A claimed contradiction is rejected when deterministic inspection establishes that at least two compound returned-dictionary keys named by the exact target claim are present; a claim for an absent payload field is not rejected by this guard. No returned gaps produces retained intermediate state without Stage 2.

Stage 2 receives the complete deduplicated gap set and may not introduce new gaps or design changes. When configured, `strict-documentation-editor` is loaded for Stage 2 only. Ordinary mode issues one `documentation_update` request with built-in Markdown-only, minimum-change, style-preservation, no-invention, source-read-only, and target-scope constraints when no skill is active.

For a source-grounded replacement bounded to one established target claim, the resulting proposal shall add or correct semantic information rather than merely restate a subset of the claim. If an established claim contains three or more distinct inline-code contract values, a replacement shall preserve at least half of them; otherwise the proposal is skipped as destructively incomplete. This guard does not reject a concise correction that introduces a new factual value.

Update output shall contain summary, impacts, changes, assumptions, and warnings. Each change includes document path, operation, rationale, concrete content, edit type, confidence, and optional meaning, section, and anchor. Missing or invalid structured object output fails reasoning. Accepted confidence values are normalized to 0.0–1.0.

### Workflow result

Results shall contain identity and timestamps; request, targets, and sources; reasoning; proposals and reviews; application records; available validation; Git diff; counters for proposed, approved, revised, rejected, skipped, applied, and failed changes; warnings; and optional error.

Workflow statuses are pending, running, review required, completed, completed with warnings, and failed. Page states also include ready, processing, and revision required. Failed preliminary validation takes precedence; otherwise, any retained unreviewed proposal requires review regardless of accumulated warnings. Completed with warnings is a terminal status used only after no review decisions remain. Completed workflow state is removed from memory.

### Configuration

| Setting | Environment variable | Default |
| --- | --- | --- |
| Reasoning provider | `PROJECT0_REASONING_PROVIDER` | `ollama` |
| Shared Ollama model | `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` |
| Documentation model | `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | shared model or `gemma3:4b` |
| Ollama URL | `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| Ollama timeout | `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | 120 seconds |
| Log level | `PROJECT0_LOG_LEVEL` | platform default |

Ollama uses shared non-streaming `/api/chat` with structured schema, temperature 0.0, and the Documentation-specific model. Stub mode supplies deterministic reasoning output for development and tests.

## 4. Workflow and Behavior

### Context and proposal workflow

In source-grounded mode, Repository Service reads the combined target/source set and labels normalized target paths `TARGET DOCUMENTATION`; other supplied paths are `AUTHORITATIVE SOURCE`. Any read error fails the complete context build rather than using partial evidence.

In ordinary mode, Knowledge Service receives the request, supplied targets, and baseline inclusion disabled, then performs its deterministic discovery, parsing, indexing, selection, and formatting.

After context construction, the workflow performs the applicable reasoning stages, constructs and guards proposals, validates current proposal paths, retains in-memory review state, and presents proposals individually.

### Review behavior

Each proposal accepts exactly `approve`, `revise`, `reject`, or `skip`; unknown workflows/proposals and duplicate reviews are rejected. Approve, reject, and skip are passed to Repository Update Service, but only approve may write. Revise records the review, performs no write, and repopulates the original browser fields for user resubmission; it does not automatically rerun reasoning.

Approval is applied immediately per proposal, so the complete proposal set is not transactional. Successful proposals for the same file are applied in review order against the evolving workflow snapshot. Completion occurs after all proposals have decisions. Final validation then checks each unique applied path, and Git diff is requested only for those paths; no applied paths produces an empty diff. Diff generation never stages, commits, pushes, merges, branches, or opens a pull request.

### Dashboard behavior

The Dashboard shall provide ready, request, review, revision, and completion presentation; show the Documentation model in system status; display proposal paths, rationales, focused differences with three context lines, decisions, validation, warnings, errors, and counters; and keep agent content inside the shared shell. Difference presentation shall not write the repository.

## 5. Errors and Constraints

The current workflow shall not persist review state across restarts; resume lost work automatically; create or delete documents; modify non-Markdown or out-of-scope paths; apply unapproved, invalid, revised, skipped, rejected, or stale proposals; roll back final-validation failures; treat proposals transactionally; monitor repository events; analyze Git diffs automatically; commit, push, merge, branch, or open pull requests; or treat model output as authoritative evidence.

Handled I/O, runtime, type, and value failures become failed workflow or reasoning results. UI exceptions become failed page state. Unexpected conditions outside these boundaries may propagate.

## 6. Acceptance Criteria

The specification is satisfied when the agent rejects blank requests; builds the correct context for each mode; generates Stage 2 proposals only from established gaps; permits only supported Markdown updates; rejects ungrounded, ambiguous, malformed, or out-of-scope proposals; presents adequate rationale and differences; honors each decision exactly once; writes only approved, non-stale changes; preserves unrelated content and repository boundaries; reports validation without implying rollback; generates the correct applied-path diff; returns accurate status, counters, warnings, and errors; remains compatible with shared platform interfaces; and demonstrates these contracts through automated tests plus separately recorded browser or model-quality evidence where applicable.
