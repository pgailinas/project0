# Research Agent Test Results

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-10

---

## 1. Status of This Record

This file is synchronized to the Research Agent implementation and automated
test inventory on GitHub `main` at commit
`9372cc13e9c47a4b768e2ad435669403c99bec32`.

No test process was executed as part of this documentation-only repository
audit. The repository has no GitHub Actions workflow run for `main` from which
an independently verifiable current pass count can be obtained. Accordingly,
this document does not claim a new aggregate pass/skip count.

Previously recorded completion statements that were not tied to an exact
revision and command have been replaced by the verifiable coverage record
below. A future local or CI execution should append an exact run record rather
than infer success from the presence of test files.

---

## 2. Implemented Automated Coverage

The current repository contains Research Agent unit coverage for:

- request, route, UI-service, and immutable view-model behavior;
- Markdown, text, and PDF Existing Research Context ingestion;
- structured context analysis, provenance, inferred solution concepts, and
  retry behavior;
- strategy construction and bounded multi-query generation;
- Semantic Scholar, OpenAlex, OpenReview, Crossref, arXiv, and stub providers;
- provider factory selection;
- provider/query dispatch, partial failures, balancing, deduplication,
  alignment-profile filtering, statistics, and candidate trace;
- provider-specific metadata normalization;
- abstract/PDF evidence acquisition and discovery-only fallback;
- preliminary and final relevance evaluation, batch recovery, and score
  validation;
- retained-paper analysis evidence validation and retry/skip behavior;
- Research Direction Analysis evidence resolution, grounding, omission, and
  retry behavior;
- workflow selection, limits, warnings, and failure states;
- in-memory compatibility artifacts;
- Dashboard composition and system-status configuration; and
- research and reasoning data models.

Integration coverage assembles Research workflows and browser-facing routes.
Browser acceptance coverage exercises Research request, result, and
end-to-end safety scenarios.

---

## 3. Current Acceptance Scenario Inventory

The browser acceptance suite defines:

| ID | Scenario |
| --- | --- |
| `UI_RA_FUN_001` | Research Agent page, request input, and processing state |
| `UI_RA_FUN_002_A` | Research source presentation |
| `UI_RA_FUN_003_A` | Paper metadata presentation |
| `UI_RA_FUN_004_A` | Research evaluation presentation |
| `UI_RA_FUN_005_A` | Visible research result/artifact-equivalent presentation and completed workflow consistency |
| `UI_RA_AI_002_A` | Unsupported research information is not presented as supported |
| `UI_RA_SAF_001_A` | Invalid request does not start the workflow |
| `UI_RA_SAF_002_A` | Unavailable results are reported safely |

The historical test names retain the term “artifacts,” but the current template
presents consolidated Research Results cards and keeps the separate legacy
artifact panel disabled.

---

## 4. Key Regression Assertions Present

The current test suite specifically asserts:

- at most three discovery-query dimensions;
- independent dispatch of each query to each provider;
- a bounded balanced evaluation pool;
- strongest available duplicate metadata retention;
- exclusion and traceability of alignment-profile mismatches;
- eight-paper evidence shortlisting;
- preliminary ranking separated from final evidence evaluation;
- final evidence-reviewed display even when no paper reaches 0.75;
- no model scoring for evidence-free discovery-only papers;
- evaluation batches of three and one unresolved-paper retry;
- one paper-analysis validation retry followed by per-paper skip;
- Direction Analysis at two or more valid papers and at most three inputs;
- omission of ordinary invalid synthesis findings;
- rejection/retry of unsupported performance ordering;
- required evidence for speculative and non-speculative directions;
- default-enabled Research Direction Analysis;
- Research Agent-specific Ollama model display; and
- consolidated paper results in the Dashboard.

---

## 5. Gaps and Limitations

The repository evidence does not establish:

- a current aggregate pass/skip count for this exact commit;
- live availability or stable ranking from external research providers;
- model-quality equivalence across Ollama models;
- exhaustive literature coverage;
- successful OCR or context chunking, which are not implemented;
- complete PDF parsing beyond the bounded heading-based extractor; or
- server-side persistence of the browser-saved Markdown package.

The current automated tests also coexist with implementation-specific
visual/video-language candidate heuristics. Passing tests establishes the
specified heuristic behavior, not general domain-independent relevance.

There is also a current implementation/test gap in
`src/project0/dashboard/dashboard_app.py`: the built-in Research reasoning stub
has no Existing Research Context response branch, its paper-analysis response
uses the older `evidence_ids` shape and omits the current `page_number` field,
and its direction response uses `E5`/`E6` rather than generated
`context-NNN`/`literature-NNN` identifiers. The Dashboard unit test covers the
stub evaluation branch but not these later branches. Consequently, the
built-in stub is not evidence of a successful full Research workflow.

---

## 6. Next Execution Record

After running verification, record:

~~~text
Revision:
Date:
Environment:
Command:
Passed:
Failed:
Skipped:
Duration:
Environment-dependent checks:
Known limitations:
~~~

Recommended commands are provided in the Research Agent Testing Guide and
repository `TEST_COMMANDS.md`.
