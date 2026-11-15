from pytest_cuke.debug_mcp.redaction import redact_data, redact_text, redacted_environment, secret_values


def test_recognized_environment_values_are_redacted(monkeypatch):
    monkeypatch.setenv("MY_API_TOKEN", "super-secret-value")
    secrets = secret_values(("my_",))

    assert "super-secret-value" in secrets
    assert redact_text("token=super-secret-value", secrets) == "token=<redacted>"
    assert redact_data({"token": "super-secret-value", "items": ["super-secret-value"]}, secrets) == {
        "token": "<redacted>",
        "items": ["<redacted>"],
    }


def test_short_values_are_not_treated_as_secrets(monkeypatch):
    monkeypatch.setenv("MY_API_TOKEN", "abc")

    assert "abc" not in secret_values(("my_",))


def test_environment_redacts_denied_names_and_embedded_values(monkeypatch):
    monkeypatch.setenv("MY_PASSWORD", "hidden-value")
    monkeypatch.setenv("MESSAGE", "prefix hidden-value suffix")

    environment = redacted_environment(("my_",))

    assert environment["MY_PASSWORD"] == "<redacted>"
    assert environment["MESSAGE"] == "prefix <redacted> suffix"
