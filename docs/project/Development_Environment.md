# Development Environment

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Purpose and Authority

This document describes the repository-supported Project0 development environment, installation procedure, runtime configuration, and common development commands.

`pyproject.toml` is authoritative for the Python version, package metadata, and declared dependencies. Source code is authoritative for environment-variable names, defaults, entry points, ports, and startup behavior. Ubuntu, Conda, Git, GitHub, and Visual Studio Code are current project conventions rather than enforced package requirements.

Run the commands in this document from the repository root unless a command states otherwise.

## 2. Supported Development Baseline

| Component | Project baseline |
| --- | --- |
| Operating system | Ubuntu Linux; Ubuntu 24.04 LTS is the current workstation convention |
| Python | Python 3.12 or later, as required by `pyproject.toml` |
| Environment manager | Conda is the project convention |
| Package installer | `python -m pip` from the active environment |
| IDE | Visual Studio Code is recommended but not required |
| Version control | Git with GitHub as the remote repository |
| Documentation | Markdown, MkDocs, Material for MkDocs, and PyMdown Extensions |
| Browser application | FastAPI, Jinja2, python-multipart, and Uvicorn |
| Default reasoning service | A locally reachable Ollama service |

The repository does not currently declare or test a formal cross-platform support matrix. A non-Ubuntu environment may work if it supplies Python 3.12 or later and all required dependencies, but that is not an established compatibility guarantee.

## 3. Repository Layout

Project0 uses a standard Python `src` layout:

```text
project0/
├── docs/
├── skills/
├── src/
│   └── project0/
├── tests/
├── mkdocs.yml
├── pyproject.toml
├── README.md
└── TEST_COMMANDS.md
```

Python package source resides below `src/project0/`. Repository documentation resides below `docs/`, while `mkdocs.yml` defines the published documentation navigation and rendering configuration. See [Project Directory Structure](Project_Directory_Structure.md) for current package boundaries.

## 4. Declared Package Requirements

`pyproject.toml` declares these runtime dependencies:

- FastAPI
- Jinja2
- MkDocs
- Material for MkDocs
- PyMdown Extensions
- pypdf
- python-multipart
- PyYAML
- Uvicorn

The `test` optional dependency declares:

- httpx
- pytest

Browser acceptance tests also import Playwright and use pytest browser fixtures. The current `pyproject.toml` does not declare those browser-test packages or browser binaries. They must be supplied separately by the acceptance-test environment.

There is no dependency lock file in the pinned repository. Minimum versions are specified for some dependencies, while others are unpinned. Installation is therefore reproducible from the declared package set but not bit-for-bit version locked.

## 5. Create and Install the Development Environment

Create the standard Conda environment and install Project0 with its declared test extra:

```bash
conda create -n project0 python=3.12
conda activate project0
python -m pip install -e '.[test]'
```

Editable installation is the normal development mode and is required for the documented `python -m project0...` commands when the package is not otherwise installed. Installing `.[test]` includes the runtime package plus the declared pytest/httpx test dependencies.

Verify the active interpreter and package:

```bash
echo "$CONDA_DEFAULT_ENV"
which python
python --version
python -m pip show project0
python -c "import project0; print(project0.__file__)"
```

The interpreter path and imported package should resolve to the intended environment and repository checkout.

### Clean-Environment Verification

When dependencies change, validate the package definition in a new environment:

```bash
conda create -n project0-clean python=3.12
conda activate project0-clean
python -m pip install -e '.[test]'
python -c "import project0; print(project0.__file__)"
python -m pytest
```

Runtime and declared non-browser tests should not require individually installed packages beyond the repository configuration. Browser acceptance tests remain the documented exception until their dependencies are declared.

## 6. Runtime Configuration

`ProjectSettings` reads environment variables when `project0.config.settings` is imported. Shell exports and Conda environment variables both become process environment values; the application receives only the final value visible in the launched process. If a variable is absent, the source default applies.

| Variable | Source default | Purpose |
| --- | --- | --- |
| `PROJECT0_LOG_LEVEL` | `INFO` | Application console log level |
| `PROJECT0_REASONING_PROVIDER` | `ollama` | Dashboard reasoning provider; implemented values are `ollama` and `stub` |
| `PROJECT0_RESEARCH_SOURCE_PROVIDERS` | `semantic_scholar,arxiv` | Comma-separated Research source-provider names |
| `PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS` | `True` | Enable Research Direction Analysis; true strings are `1`, `true`, `yes`, and `on`, case-insensitive |
| `PROJECT0_SEMANTIC_SCHOLAR_API_KEY` | unset | Optional Semantic Scholar API key |
| `PROJECT0_CROSSREF_CONTACT_EMAIL` | unset | Optional Crossref contact email |
| `PROJECT0_OLLAMA_MODEL` | `qwen2.5:7b` | Shared Ollama model and fallback for agent-specific settings |
| `PROJECT0_RESEARCH_OLLAMA_MODEL` | shared model, then `qwen2.5:7b` | Research Agent Ollama model |
| `PROJECT0_DOCUMENTATION_OLLAMA_MODEL` | shared model, then `gemma3:4b` | Documentation Agent Ollama model |
| `PROJECT0_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama service base URL |
| `PROJECT0_OLLAMA_TIMEOUT_SECONDS` | `600.0` | Shared Ollama request timeout parsed as a floating-point value |

The Research source-provider factory supports:

- `semantic_scholar`
- `openalex`
- `openreview`
- `crossref`
- `arxiv`
- `stub`

Names are comma-separated and whitespace is trimmed. An unsupported source name causes provider assembly to raise `ValueError`. An empty configured list creates no Research providers; source execution then depends on how the workflow handles that configuration.

Settings are loaded into the module-level `SETTINGS` object at import time. Change environment values before starting the Python process; changing them after the relevant module has been imported does not refresh that object automatically.

### Temporary Shell Configuration

Use shell exports for one terminal session:

```bash
export PROJECT0_REASONING_PROVIDER=ollama
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=openalex,crossref,arxiv,openreview
export PROJECT0_LOG_LEVEL=DEBUG
python -m project0.dashboard.dashboard_app
```

### Conda-Local Configuration

Use Conda environment variables for persistent workstation-local settings:

```bash
conda env config vars set PROJECT0_SEMANTIC_SCHOLAR_API_KEY="<local-api-key>"
conda deactivate
conda activate project0
```

Reactivate the environment after changing Conda variables. Never commit real API keys, credentials, or other secrets to source, tests, documentation, shell-history examples, or configuration files.

## 7. Reasoning and Research Runtime Requirements

The default live configuration requires an Ollama service reachable at `PROJECT0_OLLAMA_BASE_URL` and the configured model or models available to that service. Repository installation does not install Ollama or download models.

Research providers may also require outbound network access to their public APIs. Semantic Scholar can operate without the optional API key, subject to provider behavior and service limits. `PROJECT0_CROSSREF_CONTACT_EMAIL` supplies the optional Crossref contact identity.

The locally qualified Project0 baseline is `qwen2.5:7b`. That is a current engineering selection for Project0's requirements, not a universal claim about model quality.

## 8. Run the Command-Line Entry Point

```bash
python -m project0.main
```

This command:

1. configures logging;
2. validates required repository directories and files;
3. creates the Platform Dispatcher; and
4. runs one general documentation-context task through the generic Workflow Engine.

It exits with status 0 after successful context construction and status 1 after startup validation, workflow, or unexpected execution failure. It does not launch the Dashboard or run an interactive Documentation or Research workflow.

Do not execute `src/project0/main.py` directly. Direct execution bypasses normal package resolution in the `src` layout and may cause imports to fail.

## 9. Run the Dashboard

```bash
python -m project0.dashboard.dashboard_app
```

Open `http://127.0.0.1:8001`.

The module entry point runs Uvicorn on loopback port 8001 with reload and application-factory mode enabled. The executable factory configures logging, constructs platform dispatchers, and registers both agent interfaces. The module-level `app` object is intentionally only the shared Dashboard shell and is not the executable agent-enabled application.

### Default Live Mode

```bash
export PROJECT0_REASONING_PROVIDER=ollama
python -m project0.dashboard.dashboard_app
```

The default Research sources are `semantic_scholar,arxiv` unless overridden. Live mode requires the Ollama and network prerequisites described above.

### Deterministic Stub Mode

```bash
export PROJECT0_REASONING_PROVIDER=stub
export PROJECT0_RESEARCH_SOURCE_PROVIDERS=stub
python -m project0.dashboard.dashboard_app
```

Stub mode supplies deterministic reasoning and source data for supported development, automated-test, and demonstration paths. It is not evidence that live-provider integration is working.

## 10. Documentation Environment

Preview the MkDocs site in a separate process:

```bash
mkdocs serve
```

MkDocs uses its default local address, `http://127.0.0.1:8000`. The Dashboard's `/documentation` route redirects to that address; starting the Dashboard does not start MkDocs.

Build documentation with warnings treated as errors:

```bash
mkdocs build --strict
```

The Markdown files under `docs/` are authoritative. The generated `site/` directory is build output and should not be treated as source documentation.

## 11. Test Environment

Run the complete pytest suite with:

```bash
python -m pytest
```

Run major layers independently with:

```bash
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/acceptance -v
```

See [Testing Guide](Testing_Guide.md) and the repository-root `TEST_COMMANDS.md` for focused commands, test-layer boundaries, live-provider caveats, and browser-test requirements.

Browser acceptance tests expect a separately running Dashboard at `http://127.0.0.1:8001`. Install the necessary Playwright pytest integration and browser binaries in the test environment before collecting those modules. These dependencies are not currently part of `.[test]`.

## 12. Startup Validation

`validate_startup()` verifies:

- the project root;
- `docs/`, `src/`, and `tests/` directories;
- `src/project0/common/` and `src/project0/config/`;
- `pyproject.toml`, `mkdocs.yml`, and `README.md`; and
- the `common` and `config` package `__init__.py` files.

Failure raises `StartupValidationError`.

Startup validation does **not** verify:

- Ollama service availability;
- model installation;
- Research-provider connectivity or credentials;
- Git branch or working-tree cleanliness;
- dependency completeness;
- Python source compilation;
- pytest results; or
- MkDocs build success.

## 13. Visual Studio Code

Visual Studio Code is the recommended editor but is not required by the package. A useful local setup is:

- select the `project0` Conda interpreter;
- enable Python language support and debugging;
- run commands in an integrated terminal opened at the repository root; and
- configure module launches such as `project0.main` or `project0.dashboard.dashboard_app`, rather than launching package files directly.

Repository-specific editor settings, if added, belong under `.vscode/`. The pinned repository does not provide an authoritative VS Code configuration.

## 14. Git and Generated Files

Use ordinary Git review practices and inspect exact changes before committing:

```bash
git pull
git status --short
git diff
git add path/to/changed-file
git commit -m "Describe the completed change"
git push
```

Do not assume a clean working tree or discard unrelated work. Stage only intended files.

Common generated or local artifacts include:

- `__pycache__/`
- `*.pyc`
- `*.egg-info/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- virtual-environment directories
- `build/`
- `dist/`
- `htmlcov/`
- `site/`

Repository ignore rules, when present, are authoritative. Generated output should not be committed unless a repository workflow explicitly requires it.

## 15. Development Verification Checklist

A configured environment should support these checks, subject to the known source issue in the next section:

```bash
python --version
python -m pip show project0
python -c "import project0; print(project0.__file__)"
python -m project0.main
python -m pytest
mkdocs build --strict
```

For Dashboard verification, start `python -m project0.dashboard.dashboard_app` and visit `http://127.0.0.1:8001` in a browser. For live-provider verification, separately confirm Ollama and the configured Research services.

Passing one check does not establish the others. In particular, successful startup validation is not a substitute for source compilation, tests, or documentation build validation.

## 16. Troubleshooting

### Package Import Failure

```bash
conda activate project0
python -m pip install -e '.[test]'
python -c "import project0; print(project0.__file__)"
```

Confirm that `which python` identifies the intended Conda interpreter and that commands are being run from the repository root.

### Ollama or Model Unavailable

Confirm that the service at `PROJECT0_OLLAMA_BASE_URL` is running and that the selected model names are installed. For deterministic supported paths, use stub mode.

### Unsupported Research Provider

Check `PROJECT0_RESEARCH_SOURCE_PROVIDERS` for spelling and commas. Supported values are `semantic_scholar`, `openalex`, `openreview`, `crossref`, `arxiv`, and `stub`.

### Invalid Timeout

`PROJECT0_OLLAMA_TIMEOUT_SECONDS` is converted with `float(...)` during settings loading. A nonnumeric value prevents configuration import; supply a valid number of seconds.

### Browser Acceptance Collection Failure

If pytest cannot import Playwright or resolve its browser fixtures, install the browser-testing dependencies and browser binaries in the acceptance environment. Start the Dashboard separately before executing browser acceptance tests.

### Dashboard Available but Documentation Link Fails

Start `mkdocs serve` in a separate terminal. The Dashboard redirects to the expected MkDocs address but does not host or launch the documentation server.

### Source Compilation Issue at the Pinned Audit Commit

At commit `da217ae42f7ceeffc95a84c6baad3dc4376a18f9`, `src/project0/interfaces/knowledge_interfaces.py` contains Markdown code-fence lines around the Python module. Consequently, `python -m compileall -q src` reports a `SyntaxError`. This is a source defect, not an environment-creation failure.

## 17. Current Environment Gaps and Future Work

The following improvements are not implemented in the pinned repository:

- declare Playwright, its pytest integration, and browser setup for acceptance testing;
- add dependency locking for reproducible versions;
- add automated environment/bootstrap commands;
- define and test a cross-platform support matrix;
- provide repository-managed editor configuration where useful;
- add continuous-integration validation;
- add containerized development support; and
- correct the fenced source file identified above.
