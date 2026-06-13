"""AllureFormatter — receives pytest_bdd_message, maps to lifecycle."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest
from attrs import define, field

from pytest_bdd.plugin.allure_formatter.message_adapter import CucumberEnvelopeAdapter

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.model.message_extension import EventEnvelope
    from pytest_bdd.model.message_registry import IdentifiableObjectRegistry

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureFormatter:
    """
    Receive pytest_bdd_message events and map to AllureLifecycle.

    Implements AllureFormatterHookSpec for cross-plugin communication.
    Follows allure-pytest-bdd's PytestBDDListener pattern (pytest_bdd_listener.py:16).
    """

    config: Config = field()
    output_dir: str = field()
    adapter: CucumberEnvelopeAdapter = field(init=False)
    _file_logger: object | None = field(default=None, init=False)
    _result_uuids: list[str] = field(factory=list, init=False)
    _registry: IdentifiableObjectRegistry = field(init=False)

    def __attrs_post_init__(self) -> None:
        from allure_commons.lifecycle import AllureLifecycle

        from pytest_bdd.model.message_registry import IdentifiableObjectRegistry

        self.adapter = CucumberEnvelopeAdapter(lifecycle=AllureLifecycle())
        self.adapter.session_container_children = self._result_uuids
        self._registry = IdentifiableObjectRegistry()

    def start(self) -> None:
        """Initialize the file logger and register with allure_commons."""
        import os
        from pathlib import Path

        import allure_commons
        from allure_commons.logger import AllureFileLogger

        output_path = Path(os.path.expandvars(self.output_dir)).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        self._file_logger = AllureFileLogger(str(output_path))
        allure_commons.plugin_manager.register(self._file_logger)

    def stop(self) -> None:
        """Unregister the file logger and write the session container."""
        import allure_commons
        from allure_commons.model2 import TestResultContainer

        if self._result_uuids:
            container = TestResultContainer(
                uuid=str(uuid4()),
                name="Test session",
                children=self._result_uuids,
            )
            allure_commons.plugin_manager.hook.report_container(container=container)

        file_logger = getattr(self, "_file_logger", None)
        if file_logger is not None:
            allure_commons.plugin_manager.unregister(file_logger)
            self._file_logger = None

    # --- Hook implementations (AllureFormatterHookSpec) ---

    @pytest.hookimpl
    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
        """Process a single Cucumber Message envelope in real-time."""
        from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

        try:
            self._registry.index_tree(message)
            projection = ExecutionMessageAdapter.deserialize(message, registry=self._registry)
            if projection.payload_kind == "gherkin_document":
                uri = getattr(projection.payload, "uri", None)
                if uri is not None:
                    cast("dict", self._registry.objects_by_id)["gherkin_document", str(uri)] = projection.payload
            self.adapter.route_envelope(projection)
        except Exception:
            logger.exception("Failed to process envelope: %s", message)

    @pytest.hookimpl
    def pytest_bdd_xdist_message_batch(self, config: Config, node: object, batch: dict[str, object]) -> None:
        """Process messages forwarded from workers in real-time on the controller."""
        from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

        worker_id = batch.get("worker_id")
        raw_envelopes = batch.get("envelopes", [])
        envelopes = raw_envelopes if isinstance(raw_envelopes, list) else []
        for envelope_dict in envelopes:
            try:
                if worker_id:
                    envelope_dict = ExecutionMessageAdapter.namespace_dict_ids(
                        envelope_dict,
                        namespace=str(worker_id),
                    )
                projection = ExecutionMessageAdapter.deserialize_dict(envelope_dict, registry=self._registry)
                self._registry.index_tree(projection.envelope)
                if projection.payload_kind == "gherkin_document":
                    uri = getattr(projection.payload, "uri", None)
                    if uri is not None:
                        cast("dict", self._registry.objects_by_id)["gherkin_document", str(uri)] = projection.payload
                self.adapter.route_envelope(projection)
            except Exception:
                logger.exception("Failed to process xdist envelope: %s", envelope_dict)

    @pytest.hookimpl
    def pytest_bdd_consume_messages(self, config: Config) -> bool:
        """Opt-in to consuming the NDJSON message stream."""
        return True

    @pytest.hookimpl
    def pytest_allure_formatter_start_step(
        self,
        config: Config,
        uuid: str,
        title: str,
        params: dict | None = None,
    ) -> None:
        """Start a new step in the current test case."""
        lifecycle = self.adapter.lifecycle
        with lifecycle.start_step(uuid=uuid) as step:
            step.name = title

    @pytest.hookimpl
    def pytest_allure_formatter_stop_step(
        self,
        config: Config,
        uuid: str,
        exc_type: type | None = None,
        exc_val: Exception | None = None,
        exc_tb: object | None = None,
    ) -> None:
        """Stop the current step."""
        lifecycle = self.adapter.lifecycle
        lifecycle.stop_step(uuid)

    @pytest.hookimpl
    def pytest_allure_formatter_attach_data(
        self,
        config: Config,
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach data to the current test case or step."""
        lifecycle = self.adapter.lifecycle
        attachment_uuid = str(uuid4())
        lifecycle.attach_data(
            uuid=attachment_uuid,
            body=body,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )

    @pytest.hookimpl
    def pytest_allure_formatter_attach_file(
        self,
        config: Config,
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach a file to the current test case or step."""
        lifecycle = self.adapter.lifecycle
        attachment_uuid = str(uuid4())
        lifecycle.attach_file(
            uuid=attachment_uuid,
            source=source,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )
