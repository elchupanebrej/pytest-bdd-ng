from __future__ import annotations

import ast
import os
import re
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration


def _assert_complete_generated_module(source):
    tree = ast.parse(source)
    compile(tree, "generated.py", "exec")
    stubs = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and any(isinstance(child, ast.Raise) for child in node.body)
    ]
    assert stubs
    marker_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "pytest_cuke.steps"
        for alias in node.names
        if alias.name == "not_implemented"
    }
    assert marker_names
    for stub in stubs:
        assert any(
            isinstance(decorator, ast.Name) and decorator.id in marker_names for decorator in stub.decorator_list
        )


@pytest.mark.parametrize("generator", ["pytest", "pytest-missing", "standalone"])
def test_generated_stubs_preserve_wip_policy_and_user_code(pytester, generator):
    pytester.makeini("[pytest]\ncuke_parser = python\n")
    feature = pytester.makefile(
        ".feature",
        policy="""Feature: Generated policy
    Scenario: policy
        Given existing setup
        Then missing result
    """,
    )
    if generator == "pytest":
        result = pytester.runpytest("--cuke-generate", "--cuke-feature", str(feature))
        assert result.ret == 0
        source = result.stdout.str()
        _assert_complete_generated_module(source)
        target = pytester.makepyfile(test_generated=source)
    else:
        original = """from pathlib import Path
from pytest_cuke import given, then, scenario

USER_SENTINEL = "keep original user text"
not_implemented = "user-owned name"

@given("existing setup")
def existing_setup():
    return USER_SENTINEL

@scenario(Path("policy.feature"), "policy")
def test_policy():
    pass
"""
        target = pytester.makepyfile(test_generated=original)
        if generator == "pytest-missing":
            missing = pytester.runpytest(
                str(target), "--cuke-no-autoload", "--cuke-generate-missing", "--cuke-feature", str(feature)
            )
            assert missing.ret == 0
            snippet = missing.stdout.str().split("Please place the code above to the test file(s):", 1)[1].strip()
            sections = re.split(r"(?m)^=+ no tests ran[^\n]*=+$", snippet)
            assert len(sections) == 2 and not sections[1].strip()
            snippet = sections[0].strip()
            _assert_complete_generated_module(snippet)
            target.write_text(original + "\n\n" + snippet + "\n", encoding="utf-8")
            compile(target.read_text(encoding="utf-8"), str(target), "exec")
        else:
            command = [
                sys.executable,
                "-m",
                "pytest_cuke.cli",
                "generate",
                "steps",
                "--feature",
                str(feature),
                "--target",
                str(target),
            ]
            result = subprocess.run(
                command,
                check=False,
                cwd=pytester.path,
                env={**os.environ, "PYTEST_ADDOPTS": ""},
                text=True,
                capture_output=True,
                timeout=45,
            )
            assert result.returncode == 0, result.stderr
            source = target.read_text(encoding="utf-8")
            assert source.startswith(original)
            _assert_complete_generated_module(source)
            before_repeat = target.read_bytes()
            repeated = subprocess.run(
                command,
                check=False,
                cwd=pytester.path,
                env={**os.environ, "PYTEST_ADDOPTS": ""},
                text=True,
                capture_output=True,
                timeout=45,
            )
            assert repeated.returncode == 0, repeated.stderr
            assert target.read_bytes() == before_repeat
    skipped = pytester.runpytest_subprocess(str(target), "--cuke-no-autoload", "--cuke-wip-status=skipped", "-q")
    skipped.assert_outcomes(skipped=1)
    assert skipped.ret == 0
    for policy in ([], ["--cuke-wip-status=failed"]):
        failed = pytester.runpytest_subprocess(str(target), "--cuke-no-autoload", "-q", *policy)
        failed.assert_outcomes(failed=1)
        assert failed.ret == 1
        assert "NotImplementedError" in failed.stdout.str()


def test_wip_skip_does_not_hide_unmarked_user_errors(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\n")
    pytester.makefile(
        ".feature",
        ordinary="""Feature: Ordinary errors
    Scenario: error
        Given an ordinary user failure
    """,
    )
    module = pytester.makepyfile(
        test_ordinary="""from pathlib import Path
from pytest_cuke import given, scenario

@given("an ordinary user failure")
def ordinary_failure():
    raise NotImplementedError("ordinary-error-sentinel")

@scenario(Path("ordinary.feature"), "error")
def test_error():
    pass
"""
    )
    failed = pytester.runpytest_subprocess(str(module), "--cuke-no-autoload", "--cuke-wip-status=skipped", "-q")
    failed.assert_outcomes(failed=1)
    assert failed.ret == 1
    assert "ordinary-error-sentinel" in failed.stdout.str()
