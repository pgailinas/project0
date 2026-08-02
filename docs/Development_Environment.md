# Development Environment

**Version:** 0.1  
**Owner:**Project0  
**Last Updated:** 2026-08-02  

---

# Purpose

This document defines the standard development environment for Project0. Its purpose is to ensure that every developer uses a consistent toolchain, directory structure, Python environment, and workflow. Following these standards improves reproducibility, reduces environment-related issues, and simplifies onboarding.

This document should be considered the authoritative reference for configuring a Project0 development workstation.

---

# Supported Development Platform

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

Future support for Windows and macOS may be added as the project matures.

---

# Repository Layout

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

# Python Environment

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

# Package Installation

Project0 is installed in **editable mode** during development.

From the repository root:

```bash
python -m pip install -e .
```

Editable installation allows source code changes to become immediately available without reinstalling the package after every modification.

Verify installation:

```bash
python -m pip show project0
```

---

# Running Project0

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

# Visual Studio Code

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

# Documentation Environment

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

# Git Workflow

Typical development workflow:

```bash
git pull

# Modify source code

git status
git add .
git commit -m "Meaningful commit message"
git push
```

Developers should maintain a clean working tree before beginning new work.

---

# Generated Files

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

# Development Verification

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

---

# Troubleshooting

## ModuleNotFoundError

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

## Incorrect Python Interpreter

Verify:

```bash
which python
```

The interpreter should point to the active Conda environment rather than `/usr/bin/python3`.

---

## Git Reports Unexpected Files

Review:

```bash
git status
```

If generated files appear, update `.gitignore` rather than committing environment-specific artifacts.

---

# Future Enhancements

As Project0 evolves, this document will be expanded to include:

* Automated environment creation.
* Dependency locking.
* Testing framework configuration.
* Code formatting and linting standards.
* Continuous Integration (CI).
* Automated documentation validation.
* Containerized development environments.
* Cross-platform installation guidance.

