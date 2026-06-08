"""
Provide IDE binding and diagnostic runtime helpers.

Responsibility:
    Provide IDE binding and diagnostic runtime helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - IdeBindingService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ide_binding_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `ide_binding_runtime`

State and side effects:
    mutates payload, source_identity, source_id_key, pickles, plugin_suffix; depends on __future__.annotations, json,
    typing.TYPE_CHECKING, pytest, cucumber_messages.Attachment.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from cucumber_messages import (
    Attachment,
    AttachmentContentEncoding,
)
from cucumber_messages import Envelope as Message

from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.compatibility.pytest import Config, Item, Session
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


class IdeBindingService(ReporterServiceBase):
    """
    Represent IDE binding and diagnostic service state.

    Responsibility:
        Represent IDE binding and diagnostic service state. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - pytest_collection_modifyitems: owns nested behavior below this boundary
        - record_test_case_id: owns nested behavior below this boundary
        - mark_test_case_binding_error: owns nested behavior below this boundary
        - has_test_case_binding_error: owns nested behavior below this boundary
        - _emit_attachment: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `IdeBindingService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `IdeBindingService`

    State and side effects:
        mutates payload, source_identity, source_id_key, pickles, plugin_suffix.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    plugin_suffix = "ide_binding"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """
        Initialize the IDE binding service.

        Responsibility:
            Initialize the IDE binding service. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary
            - set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.lifecycle_service, self.items_by_source_identity_key, self.source_identities_by_key,
            self.test_case_ids_by_nodeid, self._test_cases_with_binding_errors.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service
        self.items_by_source_identity_key: dict[str, list[Item]] = {}
        self.source_identities_by_key: dict[str, dict[str, object]] = {}
        self.test_case_ids_by_nodeid: dict[str, str] = {}
        # Track test cases with binding errors (ambiguous/missing steps in mock-run)
        self._test_cases_with_binding_errors: set[str] = set()
        # We will also keep track of step definitions and candidates for Wave 3 diagnostics here
        self.available_step_definitions_by_test_case_id: dict[str, list[dict[str, object]]] = {}

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config: Config, items: list[Item]) -> None:
        """
        Collect all feature bindings and group items by source identity.

        Responsibility:
            Collect all feature bindings and group items by source identity. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.pytest_collection_modifyitems`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - params.get: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - binding.get_source_identity: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - self.items_by_source_identity_key.setdefault: collaborator call used by this boundary
            - list: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_collection_modifyitems`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_collection_modifyitems`

        State and side effects:
            mutates source_identity, source_id_key, pickles, run, callspec.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.pytest_collection_modifyitems`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        if self.reporter.is_disabled:
            return

        run = Run.from_stash(config.stash)

        for item in items:
            callspec = getattr(item, "callspec", None)
            if callspec is None:
                continue
            params = getattr(callspec, "params", {})
            gherkin_document = params.get("gherkin_document")
            pickle = params.get("pickle")
            feature_source = params.get("feature_source")
            if not gherkin_document or not pickle:
                continue

            binding = run.ensure_feature_binding(
                gherkin_document=gherkin_document,
                source=feature_source,
            )
            source_identity = binding.get_source_identity(pickle)
            source_id_key = json.dumps(source_identity, sort_keys=True)

            self.source_identities_by_key[source_id_key] = source_identity
            self.items_by_source_identity_key.setdefault(source_id_key, []).append(item)

        # Ensure we also list unbound pickles (zero hookups) from run bindings
        for binding in list(run.feature_bindings_by_uri.values()):
            # Compile pickles if not yet done
            id_generator = None
            try:
                pickles = list(binding.ensure_pickles(id_generator=id_generator))
            except (KeyError, TypeError, ValueError, RuntimeError):
                pickles = []

            for pickle in pickles:
                source_identity = binding.get_source_identity(pickle)
                source_id_key = json.dumps(source_identity, sort_keys=True)

                self.source_identities_by_key[source_id_key] = source_identity
                self.items_by_source_identity_key.setdefault(source_id_key, [])

    def record_test_case_id(self, nodeid: str, test_case_id: str) -> None:
        """
        Record TestCase ID for a given nodeid.

        Responsibility:
            Record TestCase ID for a given nodeid. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.record_test_case_id`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `record_test_case_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `record_test_case_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `record_test_case_id`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.test_case_ids_by_nodeid[nodeid] = test_case_id

    def mark_test_case_binding_error(self, test_case_id: str) -> None:
        """
        Mark a test case as having ambiguous or missing step binding errors.

        Responsibility:
            Mark a test case as having ambiguous or missing step binding errors. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.mark_test_case_binding_error`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._test_cases_with_binding_errors.add: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `mark_test_case_binding_error`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `mark_test_case_binding_error`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `mark_test_case_binding_error`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self._test_cases_with_binding_errors.add(test_case_id)

    def has_test_case_binding_error(self, test_case_id: str) -> bool:
        """
        Return True if this test case has recorded binding errors.

        Returns:
            True when a test case was marked with a binding error.

        Responsibility:
            Return True if this test case has recorded binding errors. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.has_test_case_binding_error`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `has_test_case_binding_error`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `has_test_case_binding_error`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `has_test_case_binding_error`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        return test_case_id in self._test_cases_with_binding_errors

    def _emit_attachment(self, config: Config, media_type: str, payload: Mapping[str, object]) -> None:
        """
        Emit one JSON attachment through the lifecycle service.

        Responsibility:
            Emit one JSON attachment through the lifecycle service. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService._emit_attachment` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.lifecycle_service._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary
            - Attachment: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_emit_attachment`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_emit_attachment`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(
                attachment=Attachment(
                    media_type=media_type,
                    body=json.dumps(payload),
                    content_encoding=AttachmentContentEncoding.identity,
                    timestamp=self.lifecycle_service.get_timestamp(),
                ),
            ),
        )

    def emit_launch_attachment(
        self,
        config: Config,
        test_case_id: str,
        pickle_id: str,
        nodeid: str,
        source_identity: dict[str, object],
    ) -> None:
        """
        Emit launch attachment containing mapping metadata.

        Responsibility:
            Emit launch attachment containing mapping metadata. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_launch_attachment`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_attachment: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `emit_launch_attachment`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `emit_launch_attachment`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `emit_launch_attachment`

        State and side effects:
            mutates payload.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_launch_attachment`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        payload: dict[str, object] = {
            "testCaseId": test_case_id,
            "pickleId": pickle_id,
            "nodeid": nodeid,
            "sourceIdentity": source_identity,
        }
        self._emit_attachment(config, "application/vnd.pytest-bdd.launch+json", payload)

    def emit_step_binding(  # noqa: PLR0913, PLR0917
        self,
        config: Config,
        test_case_id: str,
        pickle_step_id: str,
        step_definition_id: str,
        source_reference: dict[str, object],
        match_arguments: list[object],
    ) -> None:
        """
        Emit a matched step binding attachment.

        Responsibility:
            Emit a matched step binding attachment. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_step_binding` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_attachment: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `emit_step_binding`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `emit_step_binding`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `emit_step_binding`

        State and side effects:
            mutates payload.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_step_binding` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        payload: dict[str, object] = {
            "testCaseId": test_case_id,
            "pickleStepId": pickle_step_id,
            "stepDefinitionId": step_definition_id,
            "sourceReference": source_reference,
            "matchArguments": match_arguments,
        }
        self._emit_attachment(config, "application/vnd.pytest-bdd.step-binding+json", payload)

    def emit_missing_step(
        self,
        config: Config,
        test_case_id: str,
        pickle_step_id: str,
        unmatched_step_text: str,
        available_step_definitions: list[dict[str, object]],
    ) -> None:
        """
        Emit a missing-step diagnostic attachment.

        Responsibility:
            Emit a missing-step diagnostic attachment. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_missing_step` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_attachment: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `emit_missing_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `emit_missing_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `emit_missing_step`

        State and side effects:
            mutates payload.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_missing_step` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        payload: dict[str, object] = {
            "kind": "missing-step",
            "severity": "warning",
            "testCaseId": test_case_id,
            "pickleStepId": pickle_step_id,
            "unmatchedStepText": unmatched_step_text,
            "availableStepDefinitions": available_step_definitions,
        }
        self._emit_attachment(config, "application/vnd.pytest-bdd.diagnostic+json", payload)

    def emit_ambiguous_step(
        self,
        config: Config,
        test_case_id: str,
        pickle_step_id: str,
        candidates: list[dict[str, object]],
    ) -> None:
        """
        Emit an ambiguous-step diagnostic attachment.

        Responsibility:
            Emit an ambiguous-step diagnostic attachment. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_ambiguous_step`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_attachment: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `emit_ambiguous_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `emit_ambiguous_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `emit_ambiguous_step`

        State and side effects:
            mutates payload.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.emit_ambiguous_step`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        payload: dict[str, object] = {
            "kind": "ambiguous-step",
            "severity": "warning",
            "testCaseId": test_case_id,
            "pickleStepId": pickle_step_id,
            "candidates": candidates,
        }
        self._emit_attachment(config, "application/vnd.pytest-bdd.diagnostic+json", payload)

    def pytest_sessionfinish(self, session: Session) -> None:
        """
        Emit cardinality diagnostics for zero/multiple binds at the end of the session.

        Responsibility:
            Emit cardinality diagnostics for zero/multiple binds at the end of the session. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.pytest_sessionfinish`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - self._emit_attachment: collaborator call used by this boundary
            - self.items_by_source_identity_key.items: collaborator call used by this boundary
            - self.test_case_ids_by_nodeid.get: collaborator call used by this boundary
            - bindings.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_sessionfinish`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_sessionfinish`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_sessionfinish`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_sessionfinish`

        State and side effects:
            mutates config, source_identity, payload, bindings, test_case_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime.IdeBindingService.pytest_sessionfinish`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        if self.reporter.is_disabled:
            return

        config = session.config

        for source_key, items in self.items_by_source_identity_key.items():
            source_identity = self.source_identities_by_key[source_key]

            if len(items) == 0:
                # 0 hookups: unbound scenario
                payload: dict[str, object] = {
                    "kind": "unbound-scenario",
                    "severity": "warning",
                    "sourceIdentity": source_identity,
                }
                self._emit_attachment(config, "application/vnd.pytest-bdd.diagnostic+json", payload)
            elif len(items) > 1:
                # >1 hookups: duplicate bindings
                bindings = []
                for item in items:
                    test_case_id = self.test_case_ids_by_nodeid.get(item.nodeid)
                    bindings.append(
                        {
                            "nodeid": item.nodeid,
                            "testCaseId": test_case_id if test_case_id is not None else "",
                        },
                    )
                duplicate_payload: dict[str, object] = {
                    "kind": "duplicate-bindings",
                    "severity": "warning",
                    "sourceIdentity": source_identity,
                    "bindings": bindings,
                }
                self._emit_attachment(config, "application/vnd.pytest-bdd.diagnostic+json", duplicate_payload)
