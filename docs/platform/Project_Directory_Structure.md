# Project Directory Structure

**Version:** 0.10  
**Owner:** Project0  
**Last Updated:** 2026-09-16

---

## Purpose and Authority

This reference describes Project0's intentional repository architecture and
directory responsibilities. It omits generated caches and exhaustive file
inventory. Source, tests, configuration, and private repository contents are
implementation authority; generated MkDocs/GitHub Pages output is not.

## Reference Content

### High-level structure

```text
project0/
├── docs/
│   ├── index.md
│   ├── documentation-agent/
│   ├── research-agent/
│   └── platform/
├── notebooks/
│   └── Project0_Colab_Launcher.ipynb
├── skills/
│   └── strict-documentation-editor/
│       └── SKILL.md
├── src/project0/
│   ├── agents/
│   │   ├── documentation/
│   │   └── research/
│   ├── artifacts/
│   ├── common/
│   ├── config/
│   ├── dashboard/
│   ├── interfaces/
│   ├── knowledge/
│   ├── models/
│   ├── platform/
│   ├── reasoning/
│   ├── repository/
│   ├── validation/
│   └── workflow/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/
│   └── test_data/
├── mkdocs.yml
├── pyproject.toml
├── README.md
├── TEST_COMMANDS.md
└── .gitignore
```

### Directory responsibilities

| Directory | Responsibility |
| --- | --- |
| `docs/` | Authoritative Markdown and MkDocs source |
| `docs/documentation-agent/` | Documentation Agent charter through test records |
| `docs/research-agent/` | Research Agent charter through test records |
| `docs/platform/` | Shared platform design, contracts, and UI status data; project governance, environment, status, roadmap, and testing references |
| `notebooks/` | Student-access launchers, including the Google Colab environment for the Project0 codebase |
| `skills/` | Repository-local skill packages loaded by Skill Registry |
| `src/project0/agents/` | Agent-specific providers, services, routes, views, templates, and CSS |
| `src/project0/artifacts/` | Shared artifact-location behavior |
| `src/project0/common/` | Shared operational utilities such as logging/startup validation |
| `src/project0/config/` | Environment-backed application settings |
| `src/project0/dashboard/` | Shared FastAPI application, routes, shell, status, templates, and CSS |
| `src/project0/interfaces/` | Shared service and workflow protocols |
| `src/project0/knowledge/` | Repository-document parsing, indexing, selection, and formatting |
| `src/project0/models/` | Shared typed request, result, state, and value records |
| `src/project0/platform/` | Platform composition and dispatch |
| `src/project0/reasoning/` | Provider-neutral prompting, parsing, and provider implementations |
| `src/project0/repository/` | Safe repository discovery, reads, updates, and Git differences |
| `src/project0/validation/` | Documentation validators and aggregation |
| `src/project0/workflow/` | Generic, Documentation, and Research orchestration |
| `tests/unit/` | Isolated component and contract tests |
| `tests/integration/` | Assembled production-component tests |
| `tests/acceptance/` | Browser/external-boundary scenarios |
| `tests/test_data/` | Controlled test fixtures and repository targets |

### Agent and platform boundaries

Research business logic belongs under `src/project0/agents/research/`, its
coordinator under `src/project0/workflow/research_workflow.py`, models under
`src/project0/models/research_models.py`, and protocols under
`src/project0/interfaces/research_interfaces.py`. Documentation follows the
same ownership pattern for its agent UI and dedicated workflow/models.

The Dashboard owns the shared shell/status and registers agent routes. Platform
Dispatcher assembles dedicated workflows. The reusable Markdown/Link/MkDocs
Validation Service serves documentation workflows; Research uses its own
analysis/evaluation validation.

## Constraints and Notes

- Directory documentation describes stable architecture, not every repository
  file; consult the tree for exact current inventory.
- Generated MkDocs `site/` output is not authoritative.
- Research output may exist as in-memory compatibility `ResearchArtifact`
  values or browser-generated `project0_research_results.md`; neither is
  automatically written to the repository.
- Unit, integration, and acceptance directories are implemented rather than
  planned placeholders, but their presence is not execution evidence.
- Individual agents own Work Area behavior; the Dashboard owns the shared shell
  and status presentation.
