# Development Environment

**Version:** 0.6  
**Owner:** Project0  
**Last Updated:** 2026-09-14

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

Project0 uses a Python `src` layout with authoritative Markdown under `docs/`,
local skills under `skills/`, the Google Colab launcher under `notebooks/`,
package source under `src/project0/`, tests under `tests/`, and root
configuration in `pyproject.toml`, `mkdocs.yml`, `README.md`, and
`TEST_COMMANDS.md`. See [Project Directory
Structure](Project_Directory_Structure.md) for ownership boundaries.

Runtime dependencies are FastAPI, Jinja2, MkDocs, Material for MkDocs, PyMdown
Extensions, pypdf, python-multipart, PyYAML, and Uvicorn. The test extra declares
httpx and pytest. Playwright integration and browser binaries used by browser
acceptance are not declared and must be supplied separately. No lock file is
present; installation is package-set reproducible, not bit-for-bit locked.

### Installation and verification

```bash
conda create -n project0 python=3.12
conda activate project0
python -m pip install -e '.[test]'
echo "$CONDA_DEFAULT_ENV"
which python
python --version
python -m pip show project0
python -c "import project0; print(project0.__file__)"
```

Editable installation is the normal development mode. Validate dependency
changes in a new environment:

```bash
conda create -n project0-clean python=3.12
conda activate project0-clean
python -m pip install -e '.[test]'
python -c "import project0; print(project0.__file__)"
python -m pytest
```

Declared non-browser tests should require no ad hoc packages; browser acceptance
remains the documented exception.

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
qualified baseline, not a universal quality claim.

Temporary shell configuration:

```bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=openalex,crossref,arxiv,openreview
export PROJECT0_LOG_LEVEL=DEBUG
python -m project0.dashboard.dashboard_app
```

Persistent workstation-local credentials may use Conda environment variables;
reactivate after changes. Never commit or expose real secrets.

### Runtime, documentation, and tests

Ollama must be independently installed, reachable, and contain configured
models. Research providers require applicable network access.

```bash
python -m project0.main
python -m project0.dashboard.dashboard_app
mkdocs serve
mkdocs build --strict
python -m pytest
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/acceptance -v
```

The CLI validates repository structure and runs one generic context task; it
does not launch agents. Do not run files within `src/` directly. The Dashboard
runs on `127.0.0.1:8001`; MkDocs runs separately on `127.0.0.1:8000`. Stub mode
uses `PROJECT0_REASONING_PROVIDER=stub` and
`PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub`; it does not prove live integration.
Browser acceptance expects the Dashboard and separate Playwright environment.

### Google Colab environment

The repository provides `notebooks/Project0_Colab_Launcher.ipynb` so students
can view and exercise the same Project0 codebase without a local NVIDIA GPU.
The launcher runs Project0, Ollama, and the Dashboard within a Google Colab
runtime; it is not a separate or reduced implementation of Project0.

Select a Colab GPU runtime and configure the Colab secret
`PROJECT0_GITHUB_TOKEN` before running the notebook. The launcher performs this
sequence:

1. Clone or update Project0.
2. Install Project0 in the current runtime.
3. Verify the Colab GPU.
4. Install and start Ollama.
5. Load and verify `qwen2.5:7b`.
6. Configure and start Project0.
7. Open the Project0 Dashboard.
8. Optionally stop Project0.

The validated runtime used an NVIDIA L4 with approximately 23035 MiB VRAM.
Ollama ran `qwen2.5:7b` and reported `100% GPU`. The launcher explicitly sets:

```bash
PROJECT0_REASONING_PROVIDER=ollama
PROJECT0_DOCUMENTATION_OLLAMA_MODEL=qwen2.5:7b
PROJECT0_RESEARCH_SOURCE_PROVIDERS=openalex,crossref,arxiv,openreview
PROJECT0_LOG_LEVEL=DEBUG
```

Project0 listens on `127.0.0.1:8001` inside the runtime. The notebook displays
the Dashboard through Colab's embedded port proxy, so students interact with
the existing browser interface from the notebook.

Colab storage under `/content` is temporary. Deleting the runtime removes the
cloned repository, installed runtime state, downloaded Ollama models, and other
files stored there. Closing the notebook or browser tab does not necessarily
stop Project0; use the optional stop step or delete the runtime when finished.

In one observed run, the Research Agent completed in 3 minutes 41 seconds on an
NVIDIA L4, compared with roughly 12 minutes on a local NVIDIA T1000. This is a
non-guaranteed observation rather than a benchmark; runtime varies with Colab
GPU allocation, model state, source/network latency, and request complexity.
Student accessibility, rather than performance, is the purpose of the Colab
environment.

`validate_startup()` checks the project root; required project/package
directories; `pyproject.toml`, `mkdocs.yml`, and `README.md`; and selected
package initializers. It raises `StartupValidationError` but does not verify
dependencies, compilation, Git state, tests, MkDocs, Ollama/models, or provider
connectivity.

### Git, editor, and local output

Visual Studio Code should use the active Conda interpreter and module-based
launches. The repository has no authoritative `.vscode` configuration. Review
Git status/differences, stage only intended files, and preserve unrelated work.
Generated caches, environments, build/distribution output, coverage output, and
`site/` should not be committed unless a repository workflow requires them.

## Constraints and Notes

There is no formal cross-platform matrix, dependency lock, declared browser
test environment, automated bootstrap, CI, containerized setup, or managed
editor configuration.

At the pinned audit commit
`da217ae42f7ceeffc95a84c6baad3dc4376a18f9`, Markdown fences in
`src/project0/interfaces/knowledge_interfaces.py` cause
`python -m compileall -q src` to fail with `SyntaxError`. This is a source defect,
not an environment-creation failure.

For import failures, reactivate/install editable and verify `which python`. For
Ollama failures, confirm service URL/model or use supported stub paths. For
provider errors, check spelling and commas. A nonnumeric timeout prevents
settings import. For browser collection, install Playwright integration and
binaries and start the Dashboard. If the Documentation link fails, start
`mkdocs serve` separately.
