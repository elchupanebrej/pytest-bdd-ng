"""E2E conftest — imports all step definitions."""

import pytest

pytest.register_assert_rewrite(
    "pytest_bdd_testing.step.batch_collection",
    "pytest_bdd_testing.step.code_generator",
    "pytest_bdd_testing.step.compatibility",
    "pytest_bdd_testing.step.debug_mcp",
    "pytest_bdd_testing.step.development",
    "pytest_bdd_testing.step.formatters",
    "pytest_bdd_testing.step.go_parser",
    "pytest_bdd_testing.step.mimetype",
    "pytest_bdd_testing.step.scenario_reporter",
    "pytest_bdd_testing.step.struct_bdd",
    "pytest_bdd_testing.step.tag_expressions",
)

from pytest_bdd_testing.step.batch_collection import *  # noqa: F403, E402
from pytest_bdd_testing.step.code_generator import *  # noqa: F403, E402
from pytest_bdd_testing.step.compatibility import *  # noqa: F403, E402
from pytest_bdd_testing.step.debug_mcp import *  # noqa: F403, E402
from pytest_bdd_testing.step.development import *  # noqa: F403, E402
from pytest_bdd_testing.step.formatters import *  # noqa: F403, E402
from pytest_bdd_testing.step.go_parser import *  # noqa: F403, E402
from pytest_bdd_testing.step.harness import *  # noqa: F403, E402
from pytest_bdd_testing.step.mimetype import *  # noqa: F403, E402
from pytest_bdd_testing.step.scenario_reporter import *  # noqa: F403, E402
from pytest_bdd_testing.step.struct_bdd import *  # noqa: F403, E402
from pytest_bdd_testing.step.tag_expressions import *  # noqa: F403, E402
