"""E2E wrapper to load and execute BDD scenarios for the 18 Development space."""

import pytest
from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios(
    "18 Development/01 Allure Converter CLI.feature.md",
    "18 Development/02 Headings Validator.feature.md",
    "18 Development/03 Architecture Tooling.feature.md",
    "18 Development/04 Compatibility Matrix.feature.md",
    "18 Development/05 Messages Contract Schema Sync.feature.md",
    "18 Development/06 Cucumber Formatter Renderer.feature.md",
    "18 Development/07 Messages Coverage Audit.feature.md",
)
