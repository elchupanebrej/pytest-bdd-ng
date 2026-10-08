"""Transport Allure API calls from xdist workers through Cucumber Messages."""

from __future__ import annotations

import base64
import json
import mimetypes
import traceback
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any

import pytest

from pytest_cuke.model.message_types import Attachment, ContentEncoding, Envelope

if TYPE_CHECKING:
    from pytest import Config


ALLURE_API_STEP_MEDIA_TYPE = "application/vnd.pytest-cuke.allure-api-step+json"
ALLURE_API_ATTACHMENT_MEDIA_TYPE = "application/vnd.pytest-cuke.allure-api-attachment+json"


class NativeAllureWorkerDependencyError(RuntimeError):
    """The optional Allure runtime is required for worker event transport."""


class NativeAllureWorkerBridge:
    """Capture Allure API calls in a worker and forward them as Messages."""

    def __init__(self, config: Config) -> None:
        try:
            self._allure_commons = import_module("allure_commons")
        except ImportError as error:
            raise NativeAllureWorkerDependencyError(
                "native Allure reporting requires the optional dependency; install pytest-cuke[allure]"
            ) from error

        self._config = config
        self._api_hooks = self._make_api_hooks()
        self._started = False
        self._test_case_started_id: str | None = None
        self._test_step_id: str | None = None
        self._nodes: dict[str, dict[str, Any]] = {}
        self._roots: dict[str, str] = {}
        self._step_stack: list[str] = []
        self._root_context: dict[str, tuple[str, str | None]] = {}

    def start(self) -> None:
        """Register the Allure API listener without creating worker files."""
        if self._started:
            return
        self._allure_commons.plugin_manager.register(self._api_hooks)
        self._started = True

    def stop(self) -> None:
        """Remove the Allure API listener during pytest teardown."""
        if not self._started:
            return
        self._allure_commons.plugin_manager.unregister(self._api_hooks)
        self._started = False
        self._test_case_started_id = None
        self._test_step_id = None
        self._nodes.clear()
        self._roots.clear()
        self._step_stack.clear()
        self._root_context.clear()

    @pytest.hookimpl
    def pytest_cuke_message(self, config: Config, message: Envelope) -> None:
        """Track active Cucumber references for subsequent API events."""
        if config is not self._config:
            return
        attachment = message.attachment
        if attachment is not None and attachment.media_type in {
            ALLURE_API_STEP_MEDIA_TYPE,
            ALLURE_API_ATTACHMENT_MEDIA_TYPE,
        }:
            return

        started = message.test_case_started
        if started is not None:
            self._test_case_started_id = started.id
            self._test_step_id = None
            self._discard_unfinished_steps()
            return

        step_started = message.test_step_started
        if step_started is not None:
            if step_started.test_case_started_id == self._test_case_started_id:
                self._test_step_id = step_started.test_step_id
            return

        step_finished = message.test_step_finished
        if step_finished is not None:
            if (
                step_finished.test_case_started_id == self._test_case_started_id
                and step_finished.test_step_id == self._test_step_id
            ):
                self._test_step_id = None
            return

        case_finished = message.test_case_finished
        if case_finished is not None and case_finished.test_case_started_id == self._test_case_started_id:
            self._test_case_started_id = None
            self._test_step_id = None
            self._discard_unfinished_steps()

    def _make_api_hooks(self) -> object:
        """Build decorated hooks after the optional package has been imported."""
        hookimpl = self._allure_commons.hookimpl
        bridge = self

        class AllureApiHooks:
            @hookimpl  # type: ignore[untyped-decorator]  # allure-python-commons does not type its Pluggy marker.
            def start_step(self, uuid: str, title: str, params: dict[str, Any] | None) -> None:
                bridge._start_step(uuid, title, params)

            @hookimpl  # type: ignore[untyped-decorator]
            def stop_step(
                self,
                uuid: str,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: Any,
            ) -> None:
                bridge._stop_step(uuid, exc_type, exc_val, exc_tb)

            @hookimpl  # type: ignore[untyped-decorator]
            def attach_data(
                self,
                body: str | bytes,
                name: str | None,
                attachment_type: Any,
                extension: str | None,
            ) -> None:
                bridge._attach_data(body, name, attachment_type, extension)

            @hookimpl  # type: ignore[untyped-decorator]
            def attach_file(
                self,
                source: str,
                name: str | None,
                attachment_type: Any,
                extension: str | None,
            ) -> None:
                bridge._attach_file(source, name, attachment_type, extension)

        return AllureApiHooks()

    def _start_step(self, api_uuid: str, title: str, params: dict[str, Any] | None) -> None:
        case_started_id = self._test_case_started_id
        if case_started_id is None:
            return

        step_node: dict[str, Any] = {
            "kind": "step",
            "name": str(title),
            "start": _now_millis(),
            "stop": 0,
            "status": "passed",
            "statusDetails": None,
            "parameters": [
                {"name": str(name), "value": str(value)}
                for name, value in (params or {}).items()
            ],
            "steps": [],
            "attachments": [],
        }

        if self._step_stack:
            parent_uuid = self._step_stack[-1]
            parent = self._nodes.get(parent_uuid)
            root_uuid = self._roots.get(parent_uuid)
            if parent is None or root_uuid is None:
                return
            parent["steps"].append(step_node)
            self._roots[api_uuid] = root_uuid
        else:
            self._roots[api_uuid] = api_uuid
            self._root_context[api_uuid] = (case_started_id, self._test_step_id)

        self._nodes[api_uuid] = step_node
        self._step_stack.append(api_uuid)

    def _stop_step(
        self,
        api_uuid: str,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        step_node = self._nodes.pop(api_uuid, None)
        root_uuid = self._roots.pop(api_uuid, None)
        if step_node is None or root_uuid is None:
            return

        with suppress(ValueError):
            self._step_stack.remove(api_uuid)

        step_node["stop"] = _now_millis()
        if exc_type is not None:
            step_node["status"] = "failed" if issubclass(exc_type, AssertionError) else "broken"
            message = str(exc_val) if exc_val is not None else exc_type.__name__
            details: dict[str, str] = {"message": message}
            if exc_tb is not None:
                details["trace"] = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            step_node["statusDetails"] = details

        if api_uuid != root_uuid:
            return

        context = self._root_context.pop(root_uuid, None)
        if context is None:
            return
        case_started_id, test_step_id = context
        if case_started_id != self._test_case_started_id:
            return
        self._emit(
            ALLURE_API_STEP_MEDIA_TYPE,
            {
                **step_node,
            },
            case_started_id,
            test_step_id,
        )

    def _attach_data(
        self,
        body: str | bytes,
        name: str | None,
        attachment_type: Any,
        extension: str | None,
    ) -> None:
        self._attach_bytes(_body_bytes(body), name, attachment_type, extension)

    def _attach_file(
        self,
        source: str,
        name: str | None,
        attachment_type: Any,
        extension: str | None,
    ) -> None:
        if self._test_case_started_id is None:
            return
        content = Path(source).read_bytes()
        self._attach_bytes(content, name, attachment_type, extension)

    def _attach_bytes(
        self,
        body: bytes,
        name: str | None,
        attachment_type: Any,
        extension: str | None,
    ) -> None:
        case_started_id = self._test_case_started_id
        if case_started_id is None:
            return

        media_type, resolved_extension = _media_type_and_extension(attachment_type, extension)
        attachment = {
            "name": name or "attachment",
            "mediaType": media_type,
            "extension": resolved_extension,
            "body": base64.b64encode(body).decode("ascii"),
            "size": len(body),
        }

        if self._step_stack:
            active_step_id = self._step_stack[-1]
            active_step = self._nodes.get(active_step_id)
            root_uuid = self._roots.get(active_step_id)
            root_context = self._root_context.get(root_uuid) if root_uuid is not None else None
            if (
                active_step is not None
                and root_context is not None
                and root_context[0] == case_started_id
            ):
                active_step["attachments"].append(attachment)
                return

        self._emit(
            ALLURE_API_ATTACHMENT_MEDIA_TYPE,
            {"kind": "attachment", **attachment},
            case_started_id,
            self._test_step_id,
        )

    def _emit(
        self,
        media_type: str,
        payload: dict[str, Any],
        test_case_started_id: str,
        test_step_id: str | None,
    ) -> None:
        if self._test_case_started_id != test_case_started_id:
            return
        self._config.hook.pytest_cuke_message(
            config=self._config,
            message=Envelope(
                attachment=Attachment(
                    body=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    content_encoding=ContentEncoding.identity,
                    media_type=media_type,
                    test_case_started_id=test_case_started_id,
                    test_step_id=test_step_id,
                )
            ),
        )

    def _discard_unfinished_steps(self) -> None:
        self._nodes.clear()
        self._roots.clear()
        self._step_stack.clear()
        self._root_context.clear()


def _now_millis() -> int:
    return time_ns() // 1_000_000


def _body_bytes(body: str | bytes) -> bytes:
    return body if isinstance(body, bytes) else body.encode("utf-8")


def _media_type_and_extension(attachment_type: Any, extension: str | None) -> tuple[str, str]:
    media_type = getattr(attachment_type, "mime_type", None)
    resolved_extension = extension or getattr(attachment_type, "extension", None)

    if isinstance(attachment_type, str):
        media_type = attachment_type
    if not isinstance(media_type, str) or not media_type:
        media_type = "application/octet-stream"
    if not isinstance(resolved_extension, str) or not resolved_extension:
        resolved_extension = mimetypes.guess_extension(media_type) or "attach"
    return media_type, resolved_extension.lstrip(".")


__all__ = [
    "ALLURE_API_ATTACHMENT_MEDIA_TYPE",
    "ALLURE_API_STEP_MEDIA_TYPE",
    "NativeAllureWorkerBridge",
    "NativeAllureWorkerDependencyError",
]
