from pytest_bdd.script.compatibility_matrix import main


def test_failure_message_contains_reason(capsys):
    code = main(["--python", "314", "--pytest", "83"])
    out = capsys.readouterr().out

    assert code == 1
    assert "incompatible pair: python_not_supported_by_pytest" in out
