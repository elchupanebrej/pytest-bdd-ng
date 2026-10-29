import json

import pytest

pytestmark = pytest.mark.integration


def test_attachment_source_and_url_reach_messages_consumer(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = features\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "attachment.feature").write_text(
        "Feature: Attachments\n  Scenario: Metadata\n    Given attachments\n", encoding="utf-8"
    )
    pytester.makeconftest(
        r"""
import json
from pathlib import Path
from pytest_cuke import given

observed = []

def pytest_cuke_attach(source_data, source_media_type, source_uri, url, as_external):
    observed.append([source_data, source_media_type, source_uri, url, as_external])

def pytest_sessionfinish(session):
    Path("attachment-observations.json").write_text(json.dumps(observed), encoding="utf-8")

@given("attachments")
def attachments(attach):
    attach("plain")
    attach(b"binary", file_name="binary.bin")
    attach("hello", media_type="text/plain", source_data="origin",
           source_media_type="text/x.cucumber.gherkin+plain", source_uri="file:origin")
    attach("linked", media_type="text/plain", as_external=True,
           url="https://example.com/attachment.txt")
    attach("linked-default", url="https://example.com/default.txt")
    attach("partial", source_data="incomplete")
"""
    )
    result = pytester.runpytest_subprocess(
        "features/attachment.feature", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    result.assert_outcomes(passed=1)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    attachments = {event["attachment"]["body"]: event["attachment"] for event in envelopes if "attachment" in event}
    assert attachments["hello"]["source"] == {
        "data": "origin",
        "mediaType": "text/x.cucumber.gherkin+plain",
        "uri": "file:origin",
    }
    assert attachments["linked"]["url"] == "https://example.com/attachment.txt"
    assert attachments["linked"]["body"] == "linked"
    assert attachments["linked-default"]["url"] == "https://example.com/default.txt"
    observed = json.loads((pytester.path / "attachment-observations.json").read_text(encoding="utf-8"))
    assert observed == [
        [None, None, None, None, False],
        [None, None, None, None, False],
        ["origin", "text/x.cucumber.gherkin+plain", "file:origin", None, False],
        [None, None, None, "https://example.com/attachment.txt", True],
        [None, None, None, "https://example.com/default.txt", False],
        ["incomplete", None, None, None, False],
    ]
    assert attachments["plain"]["contentEncoding"] == "IDENTITY"
    assert attachments["YmluYXJ5"]["contentEncoding"] == "BASE64"
    assert attachments["YmluYXJ5"]["fileName"] == "binary.bin"
    assert "source" not in attachments["partial"]
    assert not any("externalAttachment" in event for event in envelopes)


def test_attachment_source_preserves_v28_media_type_validation(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = features\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "attachment.feature").write_text(
        "Feature: Attachments\n  Scenario: Invalid source type\n    Given invalid source\n", encoding="utf-8"
    )
    pytester.makeconftest(
        r"""
from pytest_cuke import given

@given("invalid source")
def invalid_source(attach):
    attach("invalid-source", source_data="origin", source_media_type="text/plain", source_uri="file:origin")
"""
    )
    result = pytester.runpytest_subprocess(
        "features/attachment.feature", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    assert result.ret == 1
    assert "PYTEST_CUKE_MESSAGE_DIAGNOSTIC=" in result.stdout.str()
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert not any(event.get("attachment", {}).get("body") == "invalid-source" for event in envelopes)
