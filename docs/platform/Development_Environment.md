# Development Environment

**Version:** 0.8  
**Owner:** Project0  
**Last Updated:** 2026-09-19

---

## Purpose and Authority

This document defines the repository-supported Project0 development baseline,
installation, runtime configuration, commands, and troubleshooting reference.
`pyproject.toml` is authoritative for Python/package dependencies; source is
authoritative for environment names, defaults, entry points, ports, and startup
behavior. Ubuntu, Conda, Git/GitHub, and Visual Studio Code are project
conventions rather than enforced package requirements. Run commands from the
repository root unless stated otherwise.

## Reference Content

### Supported baseline and layout

| Component | Project baseline |
| --- | --- |
| Operating system | Ubuntu Linux; Ubuntu 24.04 LTS workstation convention |
| Python | 3.12 or later |
| Environment manager | Conda convention |
| Installer | `python -m pip` in the active environment |
| IDE | Visual Studio Code recommended, not required |
| Version control | Git with GitHub remote |
| Documentation | Markdown, MkDocs, Material, PyMdown Extensions |
| Browser application | FastAPI, Jinja2, python-multipart, Uvicorn |
| Default reasoning service | Locally reachable Ollama |

Project0 uses a Python `src` layout with documentation under `docs/`, local
skills under `skills/`, the Google Colab launcher under `notebooks/`, package
source under `src/project0/`, and tests under `tests/`. See [Project Directory
Structure](Project_Directory_Structure.md) for ownership boundaries.

Runtime dependencies are declared in `pyproject.toml`; the test extra declares
httpx and pytest. Playwright integration and browser binaries used by browser
acceptance must be supplied separately. No lock file is present, so installation
is package-set reproducible rather than bit-for-bit locked.

### Installation and verification

```bash
conda create -n project0 python=3.12
conda activate project0
python -m pip install -e '.[test]'
python -m pytest
```

Editable installation is the normal development mode. Validate dependency
changes in a new environment. Declared non-browser tests should require no ad
hoc packages; browser acceptance remains the documented exception.

### Runtime configuration

`ProjectSettings` reads process environment values into module-level `SETTINGS`
at import. Set values before starting Python; later environment changes do not
refresh the object.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROJECT0_LOG_LEVEL` | `INFO` | Console log level |
| `PROJECT0_REASONING_PROVIDER` | `ollama` | Implemented: `ollama`, `stub` |
| `PROJECT0_RESEARCH_SOURCE_PROVIDERS` | `semantic_scholar,arxiv` | Comma-separated sources |
| `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS` | `True` | True strings: `1`, `true`, `yes`, `on` |
| `PROJECT0_SEMANTIC_SCHOLAR_API_KEY` | unset | Optional API key |
| `PROJECT0_CROSSREF_CONTACT_EMAIL` | unset | Optional contact identity |
| `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` | Shared/fallback model |
| `PROJECT0_RESEARCH_OLLAMA_MODEL` | shared, then `qwen2.5:7b` | Research model |
| `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | shared, then `gemma3:4b` | Documentation model |
| `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama base URL |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | `600.0` | Floating-point timeout |

Research sources support `semantic_scholar`, `openalex`, `openreview`,
`crossref`, `arxiv`, and `stub`. Whitespace is trimmed; unsupported names raise
`ValueError`. An empty list assembles no providers. `qwen2.5:7b` is the locally
qualified baseline, not a universal quality claim. Never commit or expose real
secrets.

### Runtime, documentation, and tests

Ollama must be independently installed, reachable, and contain configured
models. Research providers require applicable network access.

```bash
python -m project0.main
python -m project0.dashboard.dashboard_app
mkdocs serve
mkdocs build --strict
python -m pytest
```

The CLI validates repository structure and runs one generic context task; it
does not launch agents. Do not run files within `src/` directly. The Dashboard
runs on `127.0.0.1:8001`; MkDocs runs separately on `127.0.0.1:8000`. Stub mode
uses `PROJECT0_REASONING_PROVIDER=stub` and
`PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub`; it does not prove live integration.
Browser acceptance expects the Dashboard and a separate Playwright environment.

### Google Colab environment

`notebooks/Project0_Colab_Launcher.ipynb` lets users run the same Project0
codebase in Google Colab without a local NVIDIA GPU. It is not a separate or
reduced implementation.

The launcher clones the public Project0 repository without a GitHub token.
Users select a Colab GPU runtime, then the notebook verifies Python 3.12 or
newer, removes Colab's unused `jieba` package to avoid MkDocs Material
compatibility warnings, installs Project0 in editable mode, prepares Ollama and
`qwen2.5:7b`, configures the runtime, and starts the Dashboard. Its core
configuration uses Ollama for reasoning, `qwen2.5:7b` for the Documentation
Agent, and `openalex,crossref,arxiv,openreview` for research sources.

Project0 listens on `127.0.0.1:8001` inside the runtime. The notebook starts a
Cloudflare Quick Tunnel and displays its temporary public HTTPS URL; Ollama
remains private inside Colab. The cleanup checkbox defaults to false so
**Run all** does not immediately stop the Dashboard and tunnel. When explicitly
enabled, cleanup stops both processes without deleting other runtime files.

Colab storage under `/content` is temporary. Deleting the runtime removes the
cloned repository, installed runtime state, downloaded Ollama models, and other
files stored there. Closing the notebook or browser tab does not necessarily
stop Project0; use the notebook's stop step or delete the runtime when finished.

`validate_startup()` checks the project root, required project/package
directories, selected root files, and package initializers. It raises
`StartupValidationError` but does not verify dependencies, compilation, Git
state, tests, MkDocs, Ollama/models, or provider connectivity.

### Git, editor, and local output

Visual Studio Code should use the active Conda interpreter and module-based
launches. The repository has no authoritative `.vscode` configuration. Review
Git changes, stage only intended files, and preserve unrelated work. Generated
caches, environments, build/distribution output, coverage output, and `site/`
should not be committed unless a repository workflow requires them.

## Constraints and Notes

There is no formal cross-platform matrix, dependency lock, declared browser
test environment, automated bootstrap, CI, containerized setup, or managed
editor configuration.

At the pinned audit commit
`da217ae42f7ceeffc95a84c6baad3dc4376a18f9`, Markdown fences in
`src/project0/interfaces/knowledge_interfaces.py` cause
`python -m compileall -q src` to fail with `SyntaxError`. This is a source defect,
not an environment-creation failure.

For import failures, reactivate the environment and reinstall in editable mode.
For Ollama failures, confirm the service URL and model or use supported stub
paths. For provider errors, check the configured names. A nonnumeric timeout
prevents settings import. Browser acceptance requires Playwright integration,
its browser binaries, and a running Dashboard. Documentation links require a
separately running `mkdocs serve` process.
