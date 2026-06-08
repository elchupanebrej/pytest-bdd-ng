"""Provide test e2e helpers — pytest plugin registration for E2E step libraries.

All scenario bindings have been moved to per-feature-file modules under tests/cases/e2e/e2e/test_feature_*.py.
Non-scenario tests have been moved to test_messages_fixed.py.
"""

pytest_plugins = [
    "pytest_bdd_testing.cases.e2e.steps_go_parser",
    "pytest_bdd_testing.cases.e2e.steps_tag_expressions",
    "pytest_bdd_testing.cases.e2e.steps_heading_validation",
    "pytest_bdd_testing.cases.e2e.steps_mimetype",
    "pytest_bdd_testing.cases.e2e.steps_struct_bdd",
    "pytest_bdd_testing.cases.e2e.steps_formatters",
    "pytest_bdd_testing.cases.e2e.steps_code_generator",
    "pytest_bdd_testing.cases.e2e.steps_scenario_reporter",
    "pytest_bdd_testing.cases.e2e.steps_compatibility",
    "pytest_bdd_testing.cases.e2e.steps_batch_collection",
]
