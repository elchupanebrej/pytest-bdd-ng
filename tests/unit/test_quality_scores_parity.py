import json
import subprocess
import sys
from pathlib import Path

from scripts import collect_test_scores, inject_test_docstrings


def test_unassessed_templates_are_counted_but_do_not_change_averages(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    path = tests / "test_sample.py"
    path.write_text("def test_unassessed():\n    pass\n")
    assert inject_test_docstrings.inject_templates_to_test_functions(path) == 1
    generated = path.read_text()
    for criterion in collect_test_scores.TEST_SCORE_CRITERIA:
        assert f"#test-eval:{criterion}=N/A" in generated
    with path.open("a") as file:
        file.write('\n\ndef test_assessed():\n    """Test target:\\n    Example\\nTest type:\\n    Unit\\n#test-eval:isolation=4"""\n    pass\n')
    entries = collect_test_scores.collect_entries([tests])
    assert len(entries) == 2
    empty = next(entry for entry in entries if "test_unassessed" in entry.file)
    assert empty.scores == {} and empty.average is None
    output = tmp_path / "scores.json"
    monkeypatch.setattr(collect_test_scores, "TEST_REPORT_JSON", output)
    collect_test_scores.write_report(entries)
    stats = json.loads(output.read_text())["stats"]
    assert stats["total_entities"] == 2
    assert stats["averages"]["isolation"] == 4
    assert stats["averages"]["determinism"] is None
    assert stats["scored_by_criterion"]["isolation"] == 1
    assert stats["scored_by_criterion"]["determinism"] == 0

    command = Path(__file__).resolve().parents[2] / "scripts" / "arch.py"
    result = subprocess.run(
        [sys.executable, str(command), "collect-test-scores", "--root", str(tests), "--markdown"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Average score: 4.00" in result.stdout
    assert "test_unassessed" in result.stdout and "N/A" in result.stdout


def test_async_test_functions_receive_and_lose_templates(tmp_path):
    path = tmp_path / "test_async.py"
    path.write_text("async def test_async_case():\n    assert True\n")

    assert inject_test_docstrings.inject_templates_to_test_functions(path) == 1
    generated = path.read_text()
    assert "Test target:" in generated
    assert "#test-eval:isolation=N/A" in generated

    assert inject_test_docstrings.strip_template_from_function_docstring(path) == 1
    stripped = path.read_text()
    assert "Test target:" not in stripped
    assert "async def test_async_case" in stripped


def test_list_test_stubs_finds_missing_unfilled_and_unassessed(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_missing.py").write_text("def test_missing_template():\n    pass\n")
    unfilled = tests / "test_unfilled.py"
    unfilled.write_text("def test_unfilled_template():\n    pass\n")
    assert inject_test_docstrings.inject_templates_to_test_functions(unfilled) == 1
    (tests / "test_assessed.py").write_text(
        "def test_assessed():\n"
        '    """Test target:\n'
        "    Protects the scoring contract\n"
        "Test type:\n"
        "    Unit\n"
        "Test scenario:\n"
        "    Given a test, when scores are collected, then they are counted\n"
        "BDD reference:\n"
        "    None\n"
        "Fixtures:\n"
        "    - None\n"
        "Mocks:\n"
        "    - None\n"
        "Side effects:\n"
        "    None\n"
        "Reduction:\n"
        "    Cannot run lower\n"
        "Escalation:\n"
        "    Cannot run higher\n"
        "Atomicity:\n"
        "    Single assertion\n"
        "Autonomy:\n"
        "    Independent test\n"
        "Test quality score:\n"
        "    #test-eval:isolation=4\n"
        "    #test-eval:determinism=5\n"
        "    #test-eval:setup_complexity=1\n"
        "    #test-eval:assertions_clarity=5\n"
        '    """\n'
        "    pass\n",
    )

    stubs = collect_test_scores.find_test_stubs([tests])
    by_name = {stub.function: stub for stub in stubs}
    assert set(by_name) == {"test_missing_template", "test_unfilled_template"}
    assert by_name["test_missing_template"].missing_template is True
    assert by_name["test_unfilled_template"].missing_template is False
    assert "Test target" in by_name["test_unfilled_template"].unfilled_text
    assert "Test type" in by_name["test_unfilled_template"].unfilled_text
    assert by_name["test_unfilled_template"].unassessed_criteria == tuple(collect_test_scores.TEST_SCORE_CRITERIA)

    command = Path(__file__).resolve().parents[2] / "scripts" / "arch.py"
    result = subprocess.run(
        [sys.executable, str(command), "list-test-stubs", "--root", str(tests), "--json"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["total"] == 2
    names = {stub["function"] for stub in payload["stubs"]}
    assert names == set(by_name)
