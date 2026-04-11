Quickstart Guide
================

This guide helps you get started with pytest-bdd-ng using the standardized `uv` workflow.

Prerequisites
-------------

- Python 3.10 or higher
- `uv` installed (https://docs.astral.sh/uv/)

Installation
------------

1. Clone the repository:
   ```bash
   git clone https://github.com/elchupanebrej/pytest-bdd-ng.git
   cd pytest-bdd-ng
   ```

2. Install dependencies using uv:
   ```bash
   uv pip install -e .
   ```

3. Install development dependencies:
   ```bash
   uv pip install -e ".[test,testtypes,doc-gen,struct-bdd]"
   ```

Running Tests
-------------

To run the test suite using the canonical workflow:
```bash
uv run tox
```

For a quick test run:
```bash
uv run pytest tests/ -x
```

Development Workflow
--------------------

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests locally:
   ```bash
   uv run pytest tests/your_test_file.py
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

Available Commands
------------------

- `uv pip install <package>` - Install packages
- `uv run <command>` - Run commands in the project environment
- `uv run tox` - Run the full test suite
- `uv run pytest <test_path>` - Run specific tests
- `uv pip list` - List installed packages

For more detailed information, see the full documentation.