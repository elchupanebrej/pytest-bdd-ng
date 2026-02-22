from pytest_bdd.script.compatibility_matrix import main


def test_failure_message_contains_reason(capsys):
    code = main(["--python", "314", "--pytest", "83"])
    out = capsys.readouterr().out

    assert code == 1
    assert "unsupported pair: python_not_supported_by_pytest" in out


def test_failure_message_contains_eol_reason(capsys):
    code = main(["--python", "39", "--pytest", "90"])
    out = capsys.readouterr().out

    assert code == 1
    assert "unsupported pair: eol_python" in out
