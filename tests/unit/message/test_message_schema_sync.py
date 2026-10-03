from __future__ import annotations

import io
import json
import urllib.error
import urllib.request

import pytest

from pytest_cuke import message_schema_sync


class _Response(io.BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_upstream_tag_verification_follows_annotated_tag_to_pinned_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    release = message_schema_sync.UPSTREAM_RELEASES["0.1.0"]
    tag_object_sha = "a" * 40
    responses = iter(
        (
            {"object": {"type": "tag", "sha": tag_object_sha}},
            {"object": {"type": "commit", "sha": release.commit}},
        )
    )
    requested_urls: list[str] = []

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _Response:
        requested_urls.append(request.full_url)
        return _Response(json.dumps(next(responses)).encode())

    monkeypatch.setattr(message_schema_sync.urllib.request, "urlopen", fake_urlopen)

    message_schema_sync._verify_upstream_tag(release)

    assert requested_urls == [
        "https://api.github.com/repos/cucumber/messages/git/ref/tags/v24.0.1",
        f"https://api.github.com/repos/cucumber/messages/git/tags/{tag_object_sha}",
    ]


def test_missing_upstream_tag_is_an_actionable_sync_error(monkeypatch: pytest.MonkeyPatch) -> None:
    release = message_schema_sync.UPSTREAM_RELEASES["0.1.0"]

    def missing_tag(request: urllib.request.Request, timeout: float) -> None:
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(message_schema_sync.urllib.request, "urlopen", missing_tag)

    with pytest.raises(message_schema_sync.SchemaSyncError, match=r"pinned upstream tag v24\.0\.1 is missing"):
        message_schema_sync._verify_upstream_tag(release)
