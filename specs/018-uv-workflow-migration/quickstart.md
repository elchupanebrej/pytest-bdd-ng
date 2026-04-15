# Quickstart Guide

**Branch**: `018-uv-workflow-migration`

This guide outlines the canonical, single-workflow setup for contributors working on `pytest-bdd-ng`, entirely powered by `uv`. It replaces all legacy `conda`, `pip`, and `virtualenv` instructions.

## Prerequisites

- Ensure you have `uv` installed on your system.
  - MacOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

## 1. Local Setup

Clone the repository and bootstrap the environment natively:

```bash
git clone https://github.com/elchupanebrej/pytest-bdd-ng.git
cd pytest-bdd-ng

# Install all dependencies (including test environments) silently and instantly
uv sync
```

## 2. Running the Test Matrix

All canonical test environments and compatibility checks remain orchestrated by `tox`, but are now executed seamlessly via `uvx`:

```bash
# List all available testing matrices
uvx tox -l

# Run a specific test environment (e.g., Python 3.14 with latest pytest)
uvx tox -e py314-pytestlatest

# Run the strict type-checking suite
uvx tox -e mypy
```

## 3. Formatting and Linting

We enforce strict formatting rules using `pre-commit`. You do not need to globally install `pre-commit`; executing it via `uvx` securely resolves it on the fly:

```bash
# Run pre-commit over all files
uvx pre-commit run --all-files
```

## 4. Internal Project Scripts

All scripts isolated under `src/pytest_bdd/script/` have been formalized under `[project.scripts]` as CLI entrypoints. This guarantees you can invoke them smoothly without manual Python path resolutions.

```bash
# Validate feature headings formatting via native entrypoint
uv run validate_feature_headings

# Test the message capability governance layer
uv run message_capability_governance
```
