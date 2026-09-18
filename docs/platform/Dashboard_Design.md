# Dashboard Design

**Version:** 1.1  
**Owner:** Project0  
**Last Updated:** 2026-09-18  
**Source Baseline:** working tree based on `e23a957a152d500649b7a8bf2702347bc308464f`

## Executive Summary

The Project0 Dashboard is a local FastAPI/Jinja2 browser application with a
persistent shared shell and separately owned Documentation and Research agent
interfaces. The configured factory registers both agents through dedicated
dispatchers; the bare factory can create only the shared shell. Routing,
navigation, configuration snapshots, and GPU status are shared, while workflow
forms and results remain agent-owned. Long-running Dashboard operations execute
through a shared, process-local background-run manager so HTTP submission
requests return before agent workflows finish.

## Purpose and Scope

This document defines the implemented Dashboard composition, shared shell,
navigation, routes, status presentation, extension boundary, responsive
behavior, and limitations. Agent forms, workflow actions, review, and result
semantics belong in the applicable agent Interface Design documents.

The design favors local browser use, one shared application shell, consistent
navigation, human review for repository-changing workflows, dispatcher reuse,
separation of presentation and workflow logic, platform ownership of shared UI,
and agent ownership of agent-specific pages. It is not an authenticated,
multi-user, remotely deployed service.

## Component Design

### Technology and application composition

The Dashboard uses FastAPI, Jinja2, CSS, browser JavaScript, and Uvicorn. Run:

```bash
python -m project0.dashboard.dashboard_app
```

`main()` runs the reload-enabled `create_project0_dashboard_app()` factory on
`127.0.0.1:8001`. That factory configures logging/provider selection, builds
separate Documentation and Research dispatchers with agent-specific model names,
constructs their UI services, and passes them to `create_dashboard_app()`.

`app = create_dashboard_app()` is intentionally a bare shared application.
Each factory call creates an independent instance. The shared factory resolves
the project root, exposes API docs at `/api/docs`, stores application paths and
supplied services, conditionally registers agent routers/CSS, registers the
shared router after agent routers, and mounts shared CSS when present. Exact
agent routes therefore precede the generic fallback.

### Shared shell and navigation

`dashboard.html` supplies Header/branding, breadcrumb, Sidebar, context toolbar,
Work Area, Footer, shared status, navigation, and overridable page blocks. Agent
pages inherit the shell and own their active content, toolbar, styles, and
scripts.

The Sidebar contains Workspace links for Project Overview and the advertised
Documentation/Research agents; persistent System Status; and Documentation,
Activity, and Settings navigation. Only Documentation has a shared route;
`/activity` and `/settings` are unimplemented. There is no dynamic agent
registry—new agents require Python composition, routes, templates, and assets.

### Project Overview and status

The overview displays project/root, phase, repository/branch, Markdown count,
platform version, recorded test/validation text, Git status, and provider.

| Value | Source or fallback |
| --- | --- |
| Repository root | Resolved application input or working directory |
| Repository name | Hard-coded `project0` |
| Git branch | `git branch --show-current`; otherwise `Unknown` |
| Git status | `git status --porcelain`; `Clean`, `Modified`, or `Unavailable` |
| Current phase | Hard-coded stale Phase 11 label |
| Documentation count | Recursive `docs/**/*.md`; otherwise `Unknown` |
| Platform version | Hard-coded `0.1.0` |
| Test/validation text | Bold fields in `docs/platform/Project0_Validation_Status.md` |
| Provider | `PROJECT0_REASONING_PROVIDER`, default `ollama` |

The Dashboard does not run tests or validation. Missing status content becomes
`Not run`/`Unavailable`; CSS classes do not verify success. The Phase 11 label
is stale relative to roadmap/status and is an implementation inconsistency.

## Interactions and Contracts

Shared routes are:

| Route | Contract |
| --- | --- |
| `GET /` | Render Project Overview |
| `GET /documentation` | Redirect 307 to `http://127.0.0.1:8000` |
| `GET /agents/{agent_identifier}` | Render fallback when no exact agent route matched |
| `GET /api/status` | Return availability and project-root information |
| `GET /api/system-status` | Return provider/model and NVIDIA GPU values |
| `GET /api/docs` | Serve generated API documentation |

The platform owns factory/route order, shell, shared navigation/status,
templates/styles, and service extension points. Agents own exact routes, forms,
dispatcher calls, view models, results/warnings/validation/differences, toolbar
actions, scripts, templates, and CSS. UI services call `PlatformDispatcher`;
the Dashboard does not duplicate workflow logic.

The shared `BackgroundRunManager` owns run identifiers, queued/running/completed/
failed lifecycle state, timestamps, worker execution, retained results, and
unexpected failure capture. Agent routes submit callables and expose agent-owned
run and status URLs. A `303 See Other` response redirects the browser from a
submission to its processing page. Processing pages restore elapsed time, poll
run state, and replace themselves with the same run URL when work reaches a
terminal state; the run page then renders the retained agent page model.

System status accepts an optional agent selector. With Ollama, Research uses
`PROJECT0_RESEARCH_OLLAMA_MODEL`, then `PROJECT0_OLLAMA_MODEL`, defaulting to
`qwen2.5:7b`; Documentation uses its agent variable, then the shared variable,
defaulting to `gemma3:4b`; other contexts default to shared `qwen2.5:7b`. Other
providers display `Not applicable`.

GPU status parses the first row of `nvidia-smi` name, utilization, used memory,
and total memory output; command, empty, or parse failures become `Unavailable`.
Agent pages poll every two seconds and separately update activity presentation.
The endpoint does not expose workflow stages, test execution, Ollama health, or
durable activity.

## Configuration and Failure Behavior

MkDocs is separate at `127.0.0.1:8000`; the Dashboard redirects to it but does
not start or host it. Unknown non-agent routes use FastAPI's normal 404.
Agent workflow implementations and dispatcher calls remain synchronous, but the
Dashboard executes them outside the originating HTTP request through the
background-run manager. Initial Research requests and Documentation request and
review submissions therefore do not hold their POST connections open.

Below 900 px, the shell becomes one column; below 640 px, Header/Footer stack,
toolbar actions wrap, and status/summary rows stack. Semantic elements,
`lang="en"`, viewport metadata, breadcrumb/toolbar/grid labels,
`aria-current`, and native controls improve accessibility but do not establish
formal compliance.

## Constraints and Verification

The shared Dashboard lacks authentication/authorization, profiles/logout, Help,
Activity and Settings pages, persistent activity/history, durable or distributed
background jobs, automatic/embedded MkDocs, deployment configuration, dark mode,
dynamic plugin/agent discovery, and configuration-only installation. Run state
and results are held in memory, are not shared across server processes, and are
lost on restart. Runs do not yet expire automatically. Each agent router uses a
single worker by default; this preserves the Research workflow's existing single
global progress snapshot and queues overlapping runs for that agent.

Unit coverage in `test_dashboard_app.py` and `test_dashboard_routes.py` addresses
factories, state, conditional registration, precedence, configuration, shell,
overview, fallbacks, redirects, status/model/GPU behavior, and unknown routes.
`test_dashboard_flow.py` covers assembled home, navigation, status, OpenAPI, and
not-found flows. Agent browser suites require the separate browser environment.
This record does not claim that tests were executed for the source baseline.
