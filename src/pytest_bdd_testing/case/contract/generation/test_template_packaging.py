"""

Provide test template packaging helpers.
"""

from pathlib import Path

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.compatibility.tomllib import loads

PROJECT_ROOT = Path(__file__).resolve().parents[5]


def _load_pyproject() -> dict:
    return loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_template_assets_are_available_through_package_resources() -> None:
    """
    Verify template assets are available through package resources.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    template_package = files("pytest_bdd.template")

    assert template_package.joinpath("test.py.jinja2").is_file()
    assert not template_package.joinpath("features_index.rst.jinja2").is_file()
    assert not template_package.joinpath("features_section.rst.jinja2").is_file()
    assert not template_package.joinpath("feature_include.rst.jinja2").is_file()


def test_pyproject_package_data_lists_jinja2_assets() -> None:
    """
    Verify pyproject package data lists jinja2 assets.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = _load_pyproject()
    template_assets = pyproject["tool"]["setuptools"]["package-data"]["pytest_bdd.template"]

    assert "test.py.jinja2" in template_assets
    assert "features_index.rst.jinja2" not in template_assets
    assert "features_section.rst.jinja2" not in template_assets
    assert "feature_include.rst.jinja2" not in template_assets
    assert "test.py.mak" not in template_assets


def test_pyproject_package_data_lists_message_schema_assets() -> None:
    """
    Verify pyproject package data lists message schema assets.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = _load_pyproject()
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["pytest_bdd.model"] == ["message_jsonschema/*.json"]


def test_pyproject_package_data_lists_testing_formatter_templates() -> None:
    """
    Verify pyproject package data lists test helper formatter templates.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = _load_pyproject()
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["pytest_bdd_testing"] == ["resources/templates/cucumber_formatters/*.j2"]


def test_release_workflow_syncs_message_schemas_before_build() -> None:
    """
    Verify release workflow syncs message schemas before build.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yaml").read_text(encoding="utf-8")

    sync_position = workflow.index("pytest_bdd.script.sync_messages_contract_schemas")
    build_position = workflow.index("python -m build")

    assert sync_position < build_position


def test_main_workflow_checks_generated_message_schemas_without_pre_commit() -> None:
    """
    Verify main workflow checks generated message schemas without pre commit.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "main.yml").read_text(encoding="utf-8")
    pre_commit_config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "Generated messages schemas are up to date" in workflow
    assert "make check-message-schemas" in workflow
    assert "sync_messages_contract_schemas" not in pre_commit_config


def test_feature_doc_pre_commit_hook_is_removed() -> None:
    """
    Verify obsolete feature doc hook is removed.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pre_commit_config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    obsolete_script = "bdd_tree" + "_to_rst"

    assert "generate-feature-doc" not in pre_commit_config
    assert obsolete_script not in pre_commit_config


def test_pyproject_declares_jinja2_and_removes_mako_runtime_dependency() -> None:
    """
    Verify pyproject declares jinja2 and removes mako runtime dependency.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"Jinja2"' in pyproject
    assert '"Mako"' not in pyproject


def test_pyproject_declares_gitpython_for_test_suite() -> None:
    """
    Verify pyproject declares gitpython for test suite.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"GitPython"' in pyproject
    assert '"GitRepo"' not in pyproject
