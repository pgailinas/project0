# Development Environment

**Version:** 0.2  
**Owner:**Project0  
**Last Updated:** 2026-08-26  

---

## Purpose

This document defines the standard development environment for Project0. Its purpose is to ensure that every developer uses a consistent toolchain, directory structure, Python environment, and workflow. Following these standards improves reproducibility, reduces environment-related issues, and simplifies onboarding.

This document should be considered the authoritative reference for configuring a Project0 development workstation.

---

## Supported Development Platform

The initial Project0 development environment is based on Ubuntu Linux.

| Component           | Standard                       |
| ------------------- | ------------------------------ |
| Operating System    | Ubuntu 24.04 LTS               |
| Python              | Python 3.12 or later           |
| Environment Manager | Conda                          |
| IDE                 | Visual Studio Code             |
| Version Control     | Git                            |
| Remote Repository   | GitHub                         |
| Documentation       | Markdown + Material for MkDocs |
| Dashboard Framework | FastAPI (planned)              |

The Project0 Dashboard Framework will use FastAPI as the browser application framework. FastAPI has been selected because it provides a typed, testable, cross-platform foundation that integrates naturally with the existing Project0 architecture. Dashboard-specific implementation will remain independent of individual AI agent user interfaces.

---

## Repository Layout

Project0 follows the standard Python **src layout**.

```text
project0/
├── docs/
├── src/
│   └── project0/
├── pyproject.toml
├── mkdocs.yml
├── README.md
└── .gitignore
```

The repository root contains project configuration and documentation, while all Python source code resides beneath the `src/project0` package.

This structure improves package isolation, prevents accidental imports from the working directory, and follows current Python packaging best practices.

---

## Python Environment

Project0 uses a dedicated Conda environment named **project0**.

Example:

```bash
conda create -n project0 python=3.12
conda activate project0
```

Verify the active environment:

```bash
echo $CONDA_DEFAULT_ENV
which python
python --version
```

The active interpreter should be the Conda environment rather than the system Python installation.

---

## Package Installation

Project0 is installed in **editable mode** during development.

From the repository root:

```bash
python -m pip install -e .
```

As Project0 evolves, all required runtime dependencies (for example, FastAPI, Jinja2, and future AI frameworks) will be declared in `pyproject.toml`.

Developers should install Project0 from the repository configuration rather than installing individual packages manually. This ensures that every development environment is created from the same authoritative dependency definition.

Verify installation:

```bash
python -m pip show project0
```

---

## Environment Reproducibility

Project0 emphasizes deterministic environment creation.

Whenever significant runtime dependencies are added, the development environment should be validated by creating a completely new Conda environment and installing Project0 solely from the repository configuration.

Example:

```bash
conda create -n project0-clean python=3.12
conda activate project0-clean

python -m pip install -e .
```

Successful installation should require no additional manual package installation.

This procedure verifies that `pyproject.toml` remains the authoritative definition of the Project0 development environment.

---

## Runtime Configuration

Project0 runtime configuration may be provided through environment variables associated with the dedicated **project0** Conda environment or through explicit shell environment variables.

The configuration precedence is:

1. Explicit shell environment variables.
2. Conda environment variables.
3. Application defaults.

Shell environment variables are appropriate for temporary development and testing overrides.

Persistent local configuration should be associated with the **project0** Conda environment.

Sensitive values such as API keys should be stored as Conda environment variables or supplied through the shell environment. Actual secret values must not be placed in source files, tests, documentation, or committed configuration.

Example:

```bash
conda env config vars set PROJECT0_SEMANTIC_SCHOLAR_API_KEY="<local-api-key>"
```

Reactivate the environment after changing Conda environment variables:

```bash
conda deactivate
conda activate project0
```

The example value is a placeholder only.

---

## Running Project0

Always execute Project0 as an installed package.

Preferred:

```bash
python -m project0.main
```

Avoid executing source files directly.

Do **not** use:

```bash
python src/project0/main.py
```

or

```bash
/usr/bin/python3 src/project0/main.py
```

Executing individual source files bypasses the package installation and may cause module import failures.

---

## Visual Studio Code

Visual Studio Code is the recommended development environment.

Recommended configuration:

* Select the **project0** Conda interpreter.
* Enable Python IntelliSense.
* Enable debugging.
* Use the integrated terminal.
* Launch Project0 as a Python module rather than an individual file.

Repository-specific VS Code settings should reside in:

```text
project0/.vscode/
```

VS Code configuration is not currently committed to the repository.

---

## Documentation Environment

Documentation is generated using MkDocs with the Material theme.

Local preview:

```bash
mkdocs serve
```

Build static documentation:

```bash
mkdocs build
```

The documentation source is maintained in the `docs/` directory.

---

## Git Workflow

Typical development workflow:

```bash
git pull

## Modify source code

git status
git add .
git commit -m "Meaningful commit message"
git push
```

Developers should maintain a clean working tree before beginning new work.

---

## Generated Files

The following artifacts are generated automatically and should not be committed.

Examples include:

* `__pycache__/`
* `*.pyc`
* `*.egg-info/`
* `.pytest_cache/`
* `.mypy_cache/`
* `build/`
* `dist/`

Repository-specific ignore rules are maintained in `.gitignore`.

---

## Development Verification

A correctly configured development environment should satisfy the following checks.

Verify package installation:

```bash
python -m pip show project0
```

Verify package import:

```bash
python -c "import project0; print(project0.__file__)"
```

Run Project0:

```bash
python -m project0.main
```

Expected output should confirm successful startup and display the detected project root.

When the Dashboard Framework becomes available:

```bash
python -m project0.dashboard.dashboard_app
```

The dashboard should start successfully and be accessible through a local web browser.

---

## Troubleshooting

### ModuleNotFoundError

Possible causes:

* Incorrect Python interpreter.
* Running source files directly.
* Editable installation not performed.
* Conda environment not activated.

Recommended solution:

```bash
conda activate project0
python -m pip install -e .
python -m project0.main
```

---

### Incorrect Python Interpreter

Verify:

```bash
which python
```

The interpreter should point to the active Conda environment rather than `/usr/bin/python3`.

---

### Git Reports Unexpected Files

Review:

```bash
git status
```

If generated files appear, update `.gitignore` rather than committing environment-specific artifacts.

---

## Future Enhancements

As Project0 evolves, this document will be expanded to include:

* Automated environment creation.
* Dependency locking.
* Dashboard Framework installation.
* Testing framework configuration.
* Code formatting and linting standards.
* Continuous Integration (CI).
* Automated documentation validation.
* Containerized development environments.
* Cross-platform installation guidance.

