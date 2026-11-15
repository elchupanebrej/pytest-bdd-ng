import json

import pytest

from pytest_cuke.http_sources import _origin, _rules


class _Config:
    def __init__(self, rules):
        self.rules = rules

    def getoption(self, name):
        return None

    def getini(self, name):
        return [json.dumps(rule) for rule in self.rules]


@pytest.mark.parametrize(
    "rules,message",
    [
        ([{"origin": "https://example.test/path"}], "origin cannot include"),
        ([{"origin": "https://example.test"}, {"origin": "https://EXAMPLE.test:443"}], "Duplicate"),
        ([{"origin": "https://example.test", "bearer": "a", "basic": {"username": "u", "password": "p"}}], "either"),
        ([{"origin": "https://example.test", "headers": {"Authorization": "a"}, "bearer": "b"}], "conflicts"),
        ([{"origin": "https://example.test", "headers": {"X-Test": "line\nbreak"}}], "line breaks"),
    ],
)
def test_invalid_server_rules_fail_without_echoing_credentials(rules, message):
    with pytest.raises(ValueError, match=message) as error:
        _rules(_Config(rules))
    assert "line\nbreak" not in str(error.value)


def test_missing_environment_variable_is_reported(monkeypatch):
    monkeypatch.delenv("CUKE_MISSING_TOKEN", raising=False)
    with pytest.raises(ValueError, match="CUKE_MISSING_TOKEN"):
        _rules(_Config([{"origin": "https://example.test", "bearer": {"env": "CUKE_MISSING_TOKEN"}}]))


def test_origin_keeps_explicit_zero_port_and_rejects_empty_url_credentials():
    assert _origin("http://example.test:0") != _origin("http://example.test")
    with pytest.raises(ValueError, match="embedded credentials"):
        _origin("http://@example.test")
