# Research Agent Test Results

**Version:** 1.0  
**Owner:** Project0  
**Last Updated:** 2026-09-19

---

## Execution Basis

This record is synchronized to the Research Agent implementation and automated
test inventory at commit
`eedad41a4a055ca79cdaf623a598103b5db902df`.

The project validation record reports a complete deterministic repository
regression of **1410 passed, 11 skipped** on 2026-09-18. The record does not
identify the exact revision, command, duration, or environment, so the result
is retained as executed validation evidence but is not attributed to the
current source baseline. It also does not establish that browser acceptance,
live-provider/model checks, Python compilation, or strict documentation builds
were executed as part of that run.

## Results Summary

The repository contains Research Agent unit, integration, and browser
acceptance coverage for:

- request handling, routes, UI services, immutable view models, Dashboard
  composition, and system-status configuration;
- immediate background-run submission and redirect, run-scoped progress and
  result lookup, elapsed-time restoration, retained submitted fields, and
  progress-state reset between requests;
- Markdown, text, and PDF context ingestion, structured context analysis,
  provenance, inferred solution concepts, and retry behavior;
- bounded query generation and Semantic Scholar, OpenAlex, OpenReview,
  Crossref, arXiv, stub, and provider-factory behavior;
- dispatch, partial failures, balancing, deduplication, alignment filtering,
  statistics, traceability, and provider metadata normalization;
- evidence acquisition, preliminary and final relevance evaluation, batching,
  recovery, validation, paper analysis, and Direction Analysis grounding;
- workflow selection, limits, warnings, failures, compatibility artifacts, and
  research and reasoning data models.

The browser acceptance inventory comprises:

| ID | Scenario |
| --- | --- |
| `UI_RA_FUN_001` | Research page, request input, and processing state |
| `UI_RA_FUN_002_A` | Research source presentation |
| `UI_RA_FUN_003_A` | Paper metadata presentation |
| `UI_RA_FUN_004_A` | Research evaluation presentation |
| `UI_RA_FUN_005_A` | Visible results and completed-workflow consistency |
| `UI_RA_AI_002_A` | Unsupported information is not presented as supported |
| `UI_RA_SAF_001_A` | Invalid request does not start the workflow |
| `UI_RA_SAF_002_A` | Unavailable results are reported safely |

Historical test names retain “artifacts,” although the current template uses
consolidated Research Results cards and disables the separate legacy panel.
The suite also contains focused assertions for query and evaluation bounds,
balanced dispatch, metadata-preserving deduplication, alignment traceability,
evidence shortlisting, evidence-free paper handling, retry/skip behavior,
grounded Direction Analysis, effective-model display, and consolidated results.

## Failures and Risks

The recorded deterministic regression does not establish live provider
availability or ranking, model-quality equivalence, exhaustive literature
coverage, OCR or context chunking, complete PDF parsing beyond the bounded
heading extractor, or server-side persistence of the browser-saved Markdown
package. Passing tests establish the specified candidate heuristics, not
general domain-independent relevance.

There is also an implementation/test gap in
`src/project0/dashboard/dashboard_app.py`: the built-in Research reasoning stub
lacks an Existing Research Context response branch; its paper-analysis response
uses the older `evidence_ids` shape and omits `page_number`; and its direction
response uses `E5`/`E6` rather than generated `context-NNN`/`literature-NNN`
identifiers. Dashboard unit coverage reaches the evaluation branch but not
these later branches, so the stub is not evidence of a successful full Research
workflow.

## Validation Decision

Coverage is present across the major Research Agent boundaries, and the
project record contains a complete deterministic regression result of 1410
passes and 11 skips. Because its exact revision and command were not recorded,
it is not proof that the audited source baseline passed. Browser acceptance,
strict documentation validation, live providers, and live model quality remain
separate verification activities unless their exact commands and results are
recorded.

## Next Verification

Run the commands in the Research Agent Testing Guide and repository
`TEST_COMMANDS.md`, then record:

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
