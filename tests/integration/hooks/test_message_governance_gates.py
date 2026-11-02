import json

import pytest

from pytest_cuke.message_capability_governance_cli import main


@pytest.mark.parametrize("fully_governed", [False, True])
@pytest.mark.parametrize("unresolved", ["pending", "implemented-without-emission"])
def test_full_governance_requires_resolved_runtime_evidence(pytester, fully_governed, unresolved):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    pytester.makefile(".feature", policy="Feature: Governance\n  Scenario: Passes\n    Given a step\n")
    pytester.makeconftest('from pytest_cuke import given\n@given("a step")\ndef a_step():\n    pass\n')
    pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q").assert_outcomes(passed=1)
    scope = pytester.path / "mandatory.txt"
    scope.write_text("meta.protocol_version\n")
    runtime = pytester.path / "runtime.txt"
    runtime.write_text("meta.protocol_version\n")
    decisions = pytester.path / "decisions.json"
    records = [{"capability_id": "meta.protocol_version", "status": "Implemented", "release_target": "34.2.1"}]
    if unresolved == "implemented-without-emission":
        records.append({"capability_id": "parse_error.message", "status": "Implemented", "release_target": "34.2.1"})
        scope.write_text("meta.protocol_version\nparse_error.message\n")
    decisions.write_text(json.dumps({"decisions": records}))
    output = pytester.path / "report.json"
    arguments = [
        "report",
        "--messages-file",
        str(pytester.path / "messages.ndjson"),
        "--input-kind",
        "runtime",
        "--decisions",
        str(decisions),
        "--mandatory-capabilities-file",
        str(scope),
        "--runtime-required-capabilities-file",
        str(runtime),
        "--require-runtime-required-covered",
        "--output",
        str(output),
    ]
    if fully_governed:
        arguments.append("--require-fully-governed")
    assert main(arguments) == int(fully_governed)
    report = json.loads(output.read_text())
    assert report["summary"]["mandatory_scope_violations"] == 0
    assert report["summary"]["runtime_required_missing"] == 0
    assert report["summary"]["blocked_capabilities"] > 0
    assert report["gates"]["passed"] is (not fully_governed)
    if unresolved == "implemented-without-emission":
        missing = next(row for row in report["capabilities"] if row["capability_id"] == "parse_error.message")
        assert missing["status"] == "Implemented"
        assert missing["observed_runtime"] is False


def test_mandatory_scope_rejects_a_partly_applicable_observed_field(pytester, capsys):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    pytester.makefile(".feature", policy="Feature: Partial policy\n  Scenario: Passes\n    Given a step\n")
    pytester.makeconftest('from pytest_cuke import given\n@given("a step")\ndef a_step():\n    pass\n')
    pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q").assert_outcomes(passed=1)
    scope = pytester.path / "scope.txt"
    scope.write_text("meta.protocol_version\n")
    decisions = pytester.path / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "capability_id": "meta.protocol_version",
                        "status": "Partly-Applicable",
                        "release_target": "34.2.1",
                        "comment": "This test describes a language and runtime model constraint.",
                        "decision_owner": "test-only owner",
                        "evidence_refs": ["proof://test-only/partial"],
                        "reviewed_at": "2026-11-02T00:00:00+00:00",
                    }
                ]
            }
        )
    )
    output = pytester.path / "report.json"
    assert (
        main(
            [
                "report",
                "--messages-file",
                str(pytester.path / "messages.ndjson"),
                "--input-kind",
                "runtime",
                "--decisions",
                str(decisions),
                "--mandatory-capabilities-file",
                str(scope),
                "--runtime-required-capabilities-file",
                str(scope),
                "--require-runtime-required-covered",
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert "mandatory scope capabilities cannot use deferred statuses" in capsys.readouterr().err
    assert not output.exists()


def test_runtime_evidence_rejects_a_nonimplementable_decision_without_replacing_output(pytester, capsys):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    pytester.makefile(".feature", policy="Feature: Conflicting policy\n  Scenario: Passes\n    Given a step\n")
    pytester.makeconftest('from pytest_cuke import given\n@given("a step")\ndef a_step():\n    pass\n')
    pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q").assert_outcomes(passed=1)
    decisions = pytester.path / "decisions.json"
    decisions.write_text(json.dumps({"decisions": [{
        "capability_id": "meta.protocol_version", "status": "Non-Implementable", "release_target": "34.2.1",
        "comment": "This is an intentionally contradictory test-only policy.",
        "decision_owner": "test-only owner", "evidence_refs": ["proof://test-only/contradiction"],
        "reviewed_at": "2026-11-02T00:00:00+00:00", "hard_limitation": "The test policy claims no native emission.",
        "recheck_trigger": "A native observation disproves the claim."
    }]}))
    output = pytester.path / "report.json"
    previous = '{"previous": true}\n'
    output.write_text(previous)
    assert main(["report", "--messages-file", str(pytester.path / "messages.ndjson"), "--input-kind", "runtime",
                 "--decisions", str(decisions), "--output", str(output)]) == 2
    error = capsys.readouterr().err
    assert "meta.protocol_version" in error
    assert "runtime evidence" in error
    assert output.read_text() == previous
