"""Provide test e2e helpers — pytest plugin registration for E2E step libraries.

All scenario bindings have been moved to per-feature-file modules under tests/cases/e2e/e2e/test_feature_*.py.
Non-scenario tests have been moved to test_messages_fixed.py.
"""

pytest_plugins = [
    "tests.cases.e2e.steps_go_parser",
    "tests.cases.e2e.steps_tag_expressions",
    "tests.cases.e2e.steps_heading_validation",
    "tests.cases.e2e.steps_mimetype",
    "tests.cases.e2e.steps_struct_bdd",
    "tests.cases.e2e.steps_formatters",
    "tests.cases.e2e.steps_code_generator",
    "tests.cases.e2e.steps_scenario_reporter",
    "tests.cases.e2e.steps_compatibility",
    "tests.cases.e2e.steps_batch_collection",
]
