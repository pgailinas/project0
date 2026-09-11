# Documentation Agent Functional Specification

**Version:** 0.5  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose

### Mission

The Documentation Agent shall provide an AI-assisted,
human-controlled workflow for synchronizing existing Markdown
documentation with explicitly supplied repository evidence or with
repository documentation selected from a user request.

### Scope

This specification defines the current executable behavior of the
Documentation Agent implemented at GitHub commit
`e4f96f4eb5f15b75018a2f3eddc399e317ef78a9`.

The agent shall generate reviewable documentation-update proposals,
apply only individually approved proposals, validate affected paths at
the implemented stages, and report the resulting Git diff. It shall be
hosted in the Project0 Dashboard while keeping workflow and repository
behavior outside the shared Dashboard Framework.

---

## 2. Functional Principles

The Documentation Agent shall:

- treat explicitly supplied source paths as read-only authoritative
  evidence;
- treat existing target Markdown as controlled documentation;
- use structured AI reasoning only for interpretive documentation work;
- enforce path, file, operation, location, and application safety
  deterministically;
- make localized, minimum-necessary changes where the proposed edit can
  be resolved safely;
- fail closed when a source-grounded proposal is unsupported or
  ambiguous;
- require an individual human decision for every accepted proposal;
- write only approved proposals; and
- report warnings and failures without representing them as successful
  application.

---

## 3. Responsibilities

The implemented Documentation Agent shall:

- accept a required documentation request;
- accept optional target-document and authoritative-source paths;
- build context through one of two documented context modes;
- perform source-grounded gap analysis when source paths are supplied;
- request schema-constrained documentation updates;
- convert valid reasoning output into reviewable proposals;
- reject unsupported proposal operations and targets;
- run deterministic source-grounded proposal safeguards;
- perform preliminary validation of accepted proposal paths;
- present proposal rationales and focused differences;
- support approve, revise, reject, and skip decisions;
- apply approved changes through the Repository Update Service;
- reject approved proposals based on stale original content;
- perform final validation of successfully applied paths;
- generate a Git diff for applied paths; and
- return structured workflow status, summary, warnings, and errors.

The agent does not automatically inspect staged or unstaged Git changes
to derive the request. It does not automatically determine source-code
impact from a Git diff. Repository evidence enters the workflow through
explicit source paths or the ordinary documentation-knowledge path.

---

## 4. Request Contract

### 4.1 Required input

`user_request` shall contain nonblank documentation instructions. The
UI Service shall trim the request and reject an empty value before
dispatch. The Platform Dispatcher shall independently reject a blank
request.

### 4.2 Optional target paths

`target_paths` shall be repository-relative strings. When supplied,
they form an exact allowlist for proposal document paths. When omitted
in an ordinary request, Knowledge Service may select relevant Markdown
documentation from the request. They are not replaced with an implicit
baseline-document list.

Source-grounded execution is expected to include target paths because
gap and proposal schemas are scoped to target documentation. If no
usable target can be established, the workflow shall not invent a safe
target.

### 4.3 Optional source paths

`source_paths` shall identify repository files treated as read-only
authoritative evidence. Supplying at least one source path activates
source-grounded two-stage behavior.

### 4.4 Workflow identifier

A caller may supply a workflow ID. Otherwise, the Platform Dispatcher
shall generate a UUID. Review and state operations shall require a
nonblank workflow ID.

### 4.5 Browser normalization

The browser request form shall accept source and target paths as
newline-separated text. Blank lines shall be discarded and surrounding
whitespace removed. Duplicate paths are not removed by route parsing.

---

## 5. Context Construction

### 5.1 Source-grounded mode

When source paths exist, the context provider shall read the combined
target and source path list through Repository Service. It shall label
each returned file as `TARGET DOCUMENTATION` when its normalized path is
in the target set and otherwise as `AUTHORITATIVE SOURCE`.

If any requested file produces a read error, source-grounded context
construction shall fail with the combined error details. The workflow
shall not silently use a partial authoritative set.

### 5.2 Ordinary mode

Without source paths, the context provider shall call Knowledge Service
with:

- the user request as query;
- supplied target paths as requested paths; and
- baseline-document inclusion disabled.

Knowledge Service shall perform its implemented deterministic discovery,
parsing, indexing, selection, and formatting behavior.

---

## 6. Reasoning Modes and Structured Output

### 6.1 Source-grounded Stage 1

The workflow shall first issue a `documentation_gap_analysis` request.
The response shall contain a summary, gap array, assumptions, and
warnings. Each gap shall identify a target document, optional existing
section, gap description, source evidence, and optional confidence.

If reasoning fails, the workflow shall return failure. If no gaps are
returned, the workflow shall retain state with no proposals and return
an intermediate result without invoking proposal generation.

The workflow shall remove exact semantic duplicates using normalized
document path, optional section, whitespace-normalized gap text, and
whitespace-normalized source evidence.

### 6.2 Source-grounded Stage 2

The deduplicated gaps shall be appended to context as the complete
established-gap set. The workflow shall issue a
`documentation_update` request instructing the provider not to introduce
additional gaps or design changes.

When a Skill Registry is configured, the workflow shall load
`strict-documentation-editor` for Stage 2. It shall not load that skill
for Stage 1.

### 6.3 Ordinary reasoning

Without source paths, the workflow shall issue one
`documentation_update` request. When no active skill is present, the
workflow shall supply built-in Markdown-only, minimum-change,
style-preservation, no-invention, source-read-only, and target-scope
constraints.

### 6.4 Update response

Documentation update output shall contain summary, impacts, proposed
changes, assumptions, and warnings. Each proposed change shall include
document path, operation, rationale, concrete proposed content, edit
type, and confidence, plus optional documentation meaning, section, and
anchor.

The Reasoning Service shall require structured object output. Missing or
invalid structured output shall become a failed reasoning result.
Confidence shall be normalized to 0.0–1.0 where the implemented parser
accepts numeric or percentage forms; provider schemas request a decimal
in that range or null.

---

## 7. Proposal Construction and Enforcement

### 7.1 Universal requirements

For every reasoning change, the workflow shall:

- require an exact target-path match when an allowlist exists;
- accept only the `update` operation;
- require the resolved path to remain inside the repository root;
- require a lowercase-normalized `.md` suffix;
- require the target to be an existing file; and
- preserve the complete original file content in the proposal.

Create and delete operations may exist in shared reasoning models but
shall be skipped by the current proposal workflow. Every rejected
proposal shall produce a warning.

### 7.2 Source-grounded content requirements

The workflow shall reject source-grounded proposed content that is a
writing instruction or description rather than concrete Markdown.

When proposed content introduces a fenced Python block into a target
section that does not already contain comparable fenced Python, the
workflow may substitute `documentation_meaning` only when it is
nonempty, concrete prose, not rationale-like, and contains no fenced
Python. Otherwise the proposal shall be skipped.

The workflow shall canonicalize a proposed fenced Python declaration
only when exactly one matching authoritative declaration can be
identified. It shall reject a proposed function, asynchronous function,
or class declaration that does not exactly match authoritative Python
source when authoritative declarations are available.

### 7.3 Location and semantic requirements

The workflow shall first attempt to locate a proposed exact section and
then use the rationale as a discovery fallback. More than one discovered
location shall be considered ambiguous.

For source-grounded work:

- an unresolved location shall require one exact, unique anchor;
- missing, absent, or repeated anchor text shall fail closed;
- a selected section shall share meaningful normalized terms with the
  rationale or proposed content;
- a semantically unsuitable section may be replaced only by one
  existing subsection having a uniquely highest positive overlap score;
  and
- ties, zero-score candidates, or non-unique recovered locations shall
  be rejected.

If a replace proposal resolves to a Markdown section but its proposed
content does not begin with the exact existing heading, the workflow
shall preserve the heading and localize the replacement beneath it.

### 7.4 Proposal edit behavior

Insert edits shall use insert-after anchor mode. Replace and delete edit
types shall use replace anchor mode at the proposal level; however, the
workflow still accepts only update operations against existing files.

---

## 8. Validation

### 8.1 Default validators

The default Documentation Workflow shall be assembled with:

- Markdown Validator;
- Link Validator; and
- MkDocs Validator.

Documentation Consistency Validator exists in Project0 but is not part
of this default validator tuple.

### 8.2 Preliminary validation

After proposals are constructed, the workflow shall validate their
repository paths before review. This validation operates on current
repository files; it does not stage each proposed edit into a candidate
tree.

A failed preliminary result shall be returned with proposals retained,
a failure status, a warning, and an error message. A
passed-with-warnings result shall add a workflow warning and preserve an
intermediate review state.

### 8.3 Final validation

After all proposals are reviewed, the workflow shall validate only paths
whose application status is `applied`. If no path was applied, final
validation shall remain absent.

Final warnings or failure shall be reported and influence workflow
status. Final validation shall not roll back an applied change.

### 8.4 Validator exceptions

Validation Service shall continue through its configured validators.
An unexpected validator exception shall be represented as a failed
validator result and error issue and included in aggregate status.

---

## 9. Review Workflow

### 9.1 Review state

The Documentation Workflow shall store intermediate state in memory by
workflow ID. State shall include the original request, targets, sources,
reasoning, proposals, earlier reviews and application records,
preliminary validation, warnings, and any error.

### 9.2 Supported decisions

Each proposal shall accept exactly one of:

- `approve`;
- `revise`;
- `reject`; or
- `skip`.

An unknown workflow, unknown proposal, or duplicate review shall be
rejected.

### 9.3 Decision effects

Approve, reject, and skip shall be passed with the proposal to
Repository Update Service. Only approve may apply a file; reject and
skip shall return skipped application status.

Revise shall append the review, retain workflow state, perform no write,
and return control to the browser. The UI shall repopulate the original
request, source paths, and target paths so the user may change and
resubmit them. Revise shall not itself invoke reasoning or automatically
generate a replacement proposal.

Approval shall be applied immediately for that proposal. It shall not
wait for every proposal decision. Therefore, the proposal set is not a
transaction and an earlier approved change may exist while later
proposals remain under review.

The workflow shall proceed to completion after every proposal has a
recorded decision.

---

## 10. Repository Application

Repository Update Service shall:

- require matching proposal and review identifiers;
- apply content only for approve;
- resolve the target beneath the configured repository root;
- require an existing Markdown file;
- compare current content with the proposal's original snapshot;
- reject stale proposals when those values differ;
- apply the artifact-location or unique-anchor operation;
- write UTF-8 content to a temporary file in the destination directory;
- atomically replace the target; and
- return applied, skipped, or failed application status.

The service shall preserve a final newline when the original file used
one. It shall attempt to remove any remaining temporary file after
application or failure.

---

## 11. Completion and Outputs

### 11.1 Git diff

When at least one path is applied, the workflow shall request a Git diff
limited to applied paths. With no applied paths, the diff shall be an
empty string.

Git diff generation shall not stage, commit, push, merge, create a
branch, or open a pull request.

### 11.2 Result contract

A workflow result shall include:

- workflow identity and timestamps;
- user request, target paths, and source paths;
- reasoning result;
- proposals and reviews;
- applied-change records;
- preliminary and final validation where available;
- Git diff;
- summary counts;
- warnings; and
- optional error message.

Summary counts shall cover proposed, approved, revised, rejected,
skipped, applied, and failed changes.

### 11.3 Status behavior

Workflow statuses are pending, running, review required, completed,
completed with warnings, and failed. Page states additionally include
ready, processing, and revision required.

A preliminary validation warning explicitly returns review-required
workflow status. Other accumulated warnings can cause the intermediate
public result to report completed-with-warnings while review state and
unreviewed proposals still exist. Consumers shall therefore inspect
proposal decisions as well as the status value.

After final completion, the workflow shall remove its stored state.

---

## 12. Dashboard Behavior

The Dashboard-hosted Documentation Agent shall:

- provide a ready page;
- accept request, source-path, and target-path inputs;
- display the Documentation-specific model in shared system status;
- show proposal path, rationale, and focused line difference;
- provide decision and feedback controls;
- show preliminary and final validation summaries and messages;
- show warnings, errors, and workflow summary counters; and
- render all agent-specific content inside the shared Dashboard shell.

The focused difference shall be constructed from the proposal's
original snapshot and candidate application result with three context
lines around changes. It is a presentation aid and shall not write the
repository.

---

## 13. Configuration

| Setting | Environment variable | Default |
|---|---|---|
| Reasoning provider | `PROJECT0_REASONING_PROVIDER` | `ollama` |
| Shared Ollama model | `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` |
| Documentation model | `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | shared model or `gemma3:4b` |
| Ollama base URL | `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| Ollama timeout | `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | 120 seconds |
| Log level | `PROJECT0_LOG_LEVEL` | platform default |

When the reasoning provider is Ollama, the Dashboard application shall
use the shared provider implementation with the Documentation-specific
model name. The Ollama provider shall use non-streaming `/api/chat`, a
structured response schema, and temperature 0.0.

When the provider is stub, the Dashboard shall supply deterministic
Documentation reasoning output for development and tests rather than
calling Ollama.

---

## 14. Persistence, Safety, and Exclusions

The current Documentation Agent shall not:

- persist review state across process restarts;
- resume a lost workflow automatically;
- create or delete documentation files through the proposal workflow;
- modify non-Markdown files;
- modify paths outside the repository or explicit target scope;
- apply unapproved, rejected, skipped, revised, invalid, or stale
  proposals;
- automatically roll back final-validation failures;
- treat all proposals as one transaction;
- monitor repository events continuously;
- analyze staged or unstaged Git diffs automatically;
- commit, push, merge, branch, or create pull requests; or
- treat model output as authoritative repository evidence.

Expected I/O, runtime, type, and value failures shall become failed
workflow or reasoning results where handled. UI-layer exceptions shall
be converted to failed page state. Unexpected conditions outside these
handled boundaries may still propagate.

---

## 15. Success Criteria

The Documentation Agent satisfies this specification when it:

- rejects blank requests;
- constructs the correct context for each reasoning mode;
- generates Stage 2 proposals only from established source-grounded
  gaps;
- restricts proposals to supported Markdown updates;
- rejects ungrounded, ambiguous, out-of-scope, or malformed proposals;
- presents sufficient rationale and difference information for review;
- honors every supported decision exactly once;
- writes only approved, non-stale proposals;
- preserves unrelated content and repository boundaries;
- reports validation at its actual implemented stages;
- reports final validation failure without claiming rollback;
- generates the correct applied-path Git diff;
- returns accurate counters, warnings, status, and errors; and
- remains compatible with the shared Project0 Dashboard and platform
  interfaces.

Success shall be demonstrated by current automated tests and, where
model quality or browser usability is involved, separately recorded
acceptance or exploratory evidence.

---

## 16. Future Enhancements

Possible future enhancements include durable workflow state,
candidate-tree validation, automatic revision generation,
multi-proposal transactions or rollback, controlled create/delete
support, Git-change impact analysis, semantic source retrieval,
repository-event monitoring, scheduled execution, multi-agent
collaboration, and optional Git publication workflows.

These items are not part of the current functional contract. They shall
not be treated as available until implemented, tested, and documented.

---

**End of Document**
