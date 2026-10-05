from __future__ import annotations

import io
import json
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from pytest_cuke import message_schema_sync


class _Response(io.BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_upstream_tag_verification_follows_annotated_tag_to_pinned_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    release = message_schema_sync.UPSTREAM_RELEASES["28.0.0"]
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
        "https://api.github.com/repos/cucumber/messages/git/ref/tags/v28.0.0",
        f"https://api.github.com/repos/cucumber/messages/git/tags/{tag_object_sha}",
    ]


def test_missing_upstream_tag_is_an_actionable_sync_error(monkeypatch: pytest.MonkeyPatch) -> None:
    release = message_schema_sync.UPSTREAM_RELEASES["28.0.0"]

    def missing_tag(request: urllib.request.Request, timeout: float) -> None:
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(message_schema_sync.urllib.request, "urlopen", missing_tag)

    with pytest.raises(message_schema_sync.SchemaSyncError, match=r"pinned upstream tag v28\.0\.0 is missing"):
        message_schema_sync._verify_upstream_tag(release)


def test_archive_rejects_windows_backslash_traversal_paths() -> None:
    release = message_schema_sync.UPSTREAM_RELEASES["28.0.0"]
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
        member = tarfile.TarInfo("messages/jsonschema/..\\..\\outside.json")
        content = b'{"type":"object"}'
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))

    archive_buffer.seek(0)
    with tarfile.open(fileobj=archive_buffer, mode="r:gz") as archive:
        with pytest.raises(message_schema_sync.SchemaSyncError, match="unsafe path"):
            message_schema_sync._schemas_from_archive(archive, release)


def test_oversized_local_schema_is_rejected_before_opening_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "schemas"
    source.mkdir()
    oversized_schema = source / "Envelope.json"
    oversized_schema.write_bytes(b" " * (message_schema_sync.MAX_SCHEMA_BYTES + 1))

    def unexpected_open(*_args: object, **_kwargs: object) -> None:
        pytest.fail("oversized schema should be rejected before opening it")

    monkeypatch.setattr(Path, "open", unexpected_open)

    with pytest.raises(message_schema_sync.SchemaSyncError, match=r"exceeds the .* byte size limit"):
        message_schema_sync._read_directory_schemas(source)
