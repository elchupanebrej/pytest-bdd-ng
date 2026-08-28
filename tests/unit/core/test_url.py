from __future__ import annotations

from pytest_bdd.util.url import is_local_url, is_url_parsable


def test_url_helpers() -> None:
    assert is_local_url("features/test.feature")
    assert not is_local_url("https://example.com/test")
    assert not is_local_url(123)
    assert is_url_parsable("https://example.com")
    assert not is_url_parsable("http://[invalid-ipv6")
