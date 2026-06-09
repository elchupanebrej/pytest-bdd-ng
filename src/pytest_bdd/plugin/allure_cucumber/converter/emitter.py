"""Emit Allure model objects as JSON files on disk."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import uuid4

import attrs

from .model import AllureAttachment, AllureContainer

if TYPE_CHECKING:
    from pathlib import Path

    from .model import AllureTestResult


def _serialize_value(obj: object) -> dict:
    """
    Recursively convert attrs/dataclass/datetime objects for JSON.

    Returns:
        JSON-serializable dictionary representation of the object.

    """
    if attrs.has(type(obj)) and not isinstance(obj, type):
        return {k: _serialize_value(v) for k, v in attrs.asdict(obj, recurse=True).items()}
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_value(item) for item in obj]
    return obj


def _result_to_dict(result: AllureTestResult) -> dict:
    """
    Convert AllureTestResult to JSON-safe dict, converting Timestamps to ints.

    Returns:
        JSON-serializable dictionary with integer millisecond timestamps.

    """
    raw = attrs.asdict(result, recurse=True)
    return _convert_timestamps(raw)


def _convert_timestamps(obj: object) -> object:
    """
    Recursively convert Timestamp-like objects to integer milliseconds.

    Returns:
        Object with Timestamp instances replaced by integer milliseconds.

    """
    if hasattr(obj, "seconds") and hasattr(obj, "nanos"):
        return int(obj.seconds * 1000 + obj.nanos / 1_000_000)
    if isinstance(obj, dict):
        return {k: _convert_timestamps(v) for k, v in obj.items() if k not in ("body", "content_encoding")}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_convert_timestamps(item) for item in obj)
    return obj


def _write_attachments_for_item(item: object, output_dir: Path) -> None:
    """Recursively write attachments for test/step/fixture results to disk."""
    attachments = getattr(item, "attachments", []) or []
    for att in attachments:
        if isinstance(att, AllureAttachment) and att.body is not None:
            ext_map = {
                "text/plain": ".txt",
                "text/html": ".html",
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/gif": ".gif",
                "application/json": ".json",
                "application/xml": ".xml",
                "video/mp4": ".mp4",
            }
            ext = ext_map.get(str(att.type).lower(), ".attach")
            if not att.source:
                att.source = f"{uuid4()}-attachment{ext}"

            file_path = output_dir / att.source
            file_path.parent.mkdir(parents=True, exist_ok=True)
            body_str = att.body
            if isinstance(body_str, dict):
                body_str = body_str.get("data", "") or ""
            else:
                body_str = str(body_str or "")

            if str(att.content_encoding).upper() == "BASE64":
                import base64

                try:
                    data = base64.b64decode(body_str)
                    file_path.write_bytes(data)
                except Exception:
                    file_path.write_text(body_str, encoding="utf-8")
            else:
                file_path.write_text(body_str, encoding="utf-8")

            try:
                att.size = file_path.stat().st_size
            except Exception:
                att.size = len(body_str)

    steps = getattr(item, "steps", []) or []
    for step in steps:
        _write_attachments_for_item(step, output_dir)


def _write_container_attachments(container: AllureContainer, output_dir: Path) -> None:
    """Write attachments for container fixtures to disk."""
    for before in container.befores:
        _write_attachments_for_item(before, output_dir)
    for after in container.afters:
        _write_attachments_for_item(after, output_dir)


def emit_results(
    results: list[AllureTestResult],
    output_dir: Path,
) -> list[Path]:
    """
    Serialize AllureTestResults to JSON files in output_dir.

    Returns:
        List of written file paths.

    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for result in results:
        _write_attachments_for_item(result, output_dir)
        file_name = f"{result.uuid}-result.json"
        file_path = output_dir / file_name
        file_path.write_text(
            json.dumps(_result_to_dict(result), indent=2),
            encoding="utf-8",
        )
        written.append(file_path)
    return written


def emit_container(
    results: list[AllureTestResult],
    output_dir: Path,
) -> Path:
    """
    Create an AllureContainer referencing all result UUIDs and write to disk.

    Returns:
        Path to the written container JSON file.

    """
    output_dir.mkdir(parents=True, exist_ok=True)
    container = AllureContainer(
        uuid=str(uuid4()),
        name="Test results",
        children=[r.uuid for r in results],
    )
    _write_container_attachments(container, output_dir)
    file_path = output_dir / f"{container.uuid}-container.json"
    raw = attrs.asdict(container, recurse=True)
    file_path.write_text(
        json.dumps(_convert_timestamps(raw), indent=2),
        encoding="utf-8",
    )
    return file_path
