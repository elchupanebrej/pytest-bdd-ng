<!-- generated-by: gsd-doc-writer -->
# Getting Started

## Prerequisites

- Python 3.10 or higher (tested through 3.14 and PyPy 3.11)
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Installation

```bash
pip install pytest-bdd-ng
```

Or with uv:

```bash
uv pip install pytest-bdd-ng
```

For reporting features, also install the Cucumber HTML formatter:

```bash
npm install @cucumber/html-formatter
```

## Quick Start

1. **Create a feature file** `features/login.feature`:

   ```gherkin
   Feature: User login
     Scenario: Successful login
       Given the user is on the login page
       When the user enters valid credentials
       Then the user should see the dashboard
   ```

2. **Create step definitions** `features/steps/login.py`:

   ```python
   from pytest_bdd import given, when, then

   @given("the user is on the login page")
   def on_login_page():
       print("Navigating to login page")

   @when("the user enters valid credentials")
   def enter_credentials():
       print("Entering credentials")

   @then("the user should see the dashboard")
   def check_dashboard():
       print("Dashboard visible")
   ```

3. **Run pytest**:

   ```bash
   pytest features/
   ```

   Expected output: 1 passed test.

## Project Layout

Feature files go in `features/` (or any directory configured via `bdd_features_base_dir`). Step definitions are Python files imported via `conftest.py`:

```
features/
├── auth/
│   └── login.feature
├── steps/
│   └── auth_steps.py
└── conftest.py          # imports step definitions
```

In `conftest.py`:

```python
from steps.auth_steps import *
```

## Common Setup Issues

1. **"No scenarios found"** — Ensure `bdd_features_base_dir` points to the correct directory and feature files have `.feature` or `.feature.md` extension.

2. **"Step definition not found"** — Verify step definitions are imported in a `conftest.py` file within the test directory hierarchy.

3. **Import errors** — Install all dependencies: `pip install pytest-bdd-ng[full]`

## Next Steps

- [DEVELOPMENT.md](DEVELOPMENT.md) — Development setup and build commands
- [TESTING.md](TESTING.md) — Running and writing tests
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and component overview
