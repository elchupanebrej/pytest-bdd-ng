"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
"""

from __future__ import annotations

import logging
import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import pytest
from cucumber_messages import (
    Envelope as Message,
)
from cucumber_messages import (
    ParameterType,
    Pickle,
    PickleStep,
    StepMatchArgumentsList,
    TestCase,
    TestStep,
)

from pytest_bdd.compatibility.pytest import Config, FixtureLookupError, FixtureRequest
from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime._static_helpers import (
    _build_candidate_dicts,
    _build_parameter_type_source_reference,
    _build_step_match_arguments_lists,
    _collect_available_defs_for_diagnostic,
)
from pytest_bdd.steps import Definition, Matcher, StepDefinitionManager
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

    from pytest_bdd.compatibility.pytest import Item
    from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


logger = logging.getLogger(__name__)


class StepCatalogService(ReporterServiceBase):
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """

    plugin_suffix = "steps"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        lifecycle_service: LifecycleService,
        hook_catalog_service: HookCatalogService,
    ) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service
        self.hook_catalog_service = hook_catalog_service

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: Item) -> Iterator[None]:  # noqa: C901, PLR0912, PLR0914, PLR0915  -- suppressed warning
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        yield
        if self.reporter.is_disabled:
            return

        session = item.session
        config: Config = session.config
        hook_handler = config.hook
        request = item._request  # noqa: SLF001  -- suppressed warning
        run = Run.from_stash(request.config.stash)
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            logger.warning(
                "Execution context unavailable during pytest_runtest_setup; "
                "skipping context-backed correlation writes.",
            )
            return
        gherkin_document, pickle = self.lifecycle_service._resolve_gherkin_document_and_pickle(run=run)  # noqa: SLF001  -- suppressed warning
        if gherkin_document is None or pickle is None:
            logger.warning("Execution context does not carry runtime feature/pickle during pytest_runtest_setup.")
            return
        runtime_pickle = cast("Pickle", pickle)

        self._report_step_definitions(config, request)
        self._register_parameter_types(config, request)
        reporting_state = run.reporting_state
        test_steps = []
        previous_step = None
        reporting_state.runtime_step_to_pickle_step_id.clear()
        matched_steps: list[tuple[PickleStep, Definition, list[StepMatchArgumentsList]]] = []
        is_mock_run: bool = bool(getattr(config.option, "mock_run", False))

        # Pre-allocate test_case_id so we can use it in mock-run diagnostics emitted before TestCase msg
        pre_test_case_id: str = next(IdGenerator.from_stash(config.stash))

        test_steps.extend(
            [
                TestStep(
                    id=next(IdGenerator.from_stash(config.stash)),
                    hook_id=hook_registration.hook_message_id,
                )
                for hook_registration in self.hook_catalog_service._iter_matching_hook_registrations(  # noqa: SLF001  -- suppressed warning
                    request=request,
                    pickle=runtime_pickle,
                )
            ],
        )

        ide_service = self.reporter.ide_binding_service

        for step in runtime_pickle.steps:  # noqa: PLR1702  -- suppressed warning
            scenario_run.step_object = step
            scenario_run.previous_step_object = previous_step  # type: ignore[assignment]  # PickleStep | None vs PickleStep | NoPreviousStep
            step_definition: Definition | None = None
            step_match_arguments_lists: list[StepMatchArgumentsList] = []
            has_ambiguity = False

            if is_mock_run:
                # Capture PytestBDDStepDefinitionWarning to detect ambiguous matches
                with warnings.catch_warnings(record=True) as caught_warnings:
                    warnings.simplefilter("always", PytestBDDStepDefinitionWarning)
                    try:
                        step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                            request=request,
                            run=run,
                        )
                    except StepDefinitionManager.Matcher.MatchNotFoundError:
                        # Missing step: collect available defs and emit diagnostic
                        available_defs = _collect_available_defs_for_diagnostic(config, request)
                        ide_service.emit_missing_step(
                            config,
                            pre_test_case_id,
                            step.id,
                            step.text,
                            available_defs,
                        )
                        ide_service.mark_test_case_binding_error(pre_test_case_id)
                    else:
                        ambig_warnings = [
                            x for x in caught_warnings if issubclass(x.category, PytestBDDStepDefinitionWarning)
                        ]
                        if ambig_warnings:
                            has_ambiguity = True
                            # Enumerate all candidates from the step_matcher`s post-call state
                            candidates: list[Definition] = []
                            with suppress(Exception):
                                step_matcher_inst = request.getfixturevalue("step_matcher")
                                candidates = list(
                                    Matcher.find_step_definition_matches(
                                        step_matcher_inst.step_registry,
                                        (
                                            step_matcher_inst.strict_matcher,
                                            step_matcher_inst.unspecified_matcher,
                                            step_matcher_inst.liberal_matcher,
                                        ),
                                    ),
                                )
                            candidate_dicts = _build_candidate_dicts(config, candidates)
                            ide_service.emit_ambiguous_step(
                                config,
                                pre_test_case_id,
                                step.id,
                                candidate_dicts,
                            )
                            ide_service.mark_test_case_binding_error(pre_test_case_id)
            else:
                with suppress(StepDefinitionManager.Matcher.MatchNotFoundError):
                    step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                        request=request,
                        run=run,
                    )

            if step_definition is not None and not has_ambiguity:
                step_match_arguments_lists = _build_step_match_arguments_lists(
                    request=request,
                    step_definition=step_definition,
                    step_text=step.text,
                )
                test_step = TestStep(
                    id=next(IdGenerator.from_stash(config.stash)),
                    pickle_step_id=step.id,
                    step_definition_ids=[step_definition.as_message(config).id],
                    **(
                        {"step_match_arguments_lists": step_match_arguments_lists} if step_match_arguments_lists else {}
                    ),
                )
                test_steps.append(test_step)
                matched_steps.append((step, step_definition, step_match_arguments_lists))
                run.map_runtime_step_to_test_step_id(
                    pickle_step=step,
                    test_step_id=test_step.id,
                )
            previous_step = step

        resolved_run_started_id = Run.from_stash(config.stash).reporting_state.run_started_id
        test_case = TestCase(
            id=pre_test_case_id,
            pickle_id=runtime_pickle.id,
            test_steps=test_steps,
            **({"test_run_started_id": resolved_run_started_id} if resolved_run_started_id is not None else {}),
        )
        reporting_state.active_test_case_id = test_case.id
        self.lifecycle_service._emit_envelope(  # noqa: SLF001  -- suppressed warning
            config,
            Message(test_case=test_case),
        )

        ide_service.record_test_case_id(item.nodeid, test_case.id)
        binding = run.feature_binding_for_document(gherkin_document)  # type: ignore[arg-type]  # stash returns untyped object
        if binding is not None:
            source_identity = binding.get_source_identity(runtime_pickle)
            ide_service.emit_launch_attachment(
                config,
                test_case.id,
                runtime_pickle.id,
                item.nodeid,
                source_identity,
            )

        # Emit per-step binding attachments for IDE consumers
        for step, step_definition, _step_match_arguments_lists in matched_steps:
            sd_message = step_definition.as_message(config)
            sr = sd_message.source_reference
            source_ref_dict: dict[str, object] = {}
            if sr is not None:
                source_ref_dict["uri"] = getattr(sr, "uri", None) or ""
                loc = getattr(sr, "location", None)
                source_ref_dict["line"] = getattr(loc, "line", 1) if loc is not None else 1
            ide_service.emit_step_binding(
                config,
                test_case.id,
                step.id,
                sd_message.id,
                source_ref_dict,
                [],
            )

    def _report_step_definitions(self, config: Config, request: FixtureRequest) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
        seen_steps: set[int] = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    step_definition_message = step_definition.as_message(config=config)
                    if step_definition_message.id in self.reporter._emitted_step_definition_ids:  # noqa: SLF001  -- suppressed warning
                        continue
                    self.reporter._emitted_step_definition_ids.add(step_definition_message.id)  # noqa: SLF001  -- suppressed warning
                    self.lifecycle_service._emit_envelope(  # noqa: SLF001  -- suppressed warning
                        config,
                        Message(step_definition=step_definition_message),
                    )
            step_registry = step_registry.parent

    def report_step_definitions(self, config: Config, request: FixtureRequest) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        self._report_step_definitions(config, request)

    def _register_parameter_types(self, config: Config, request: FixtureRequest) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
        seen_steps: set[int] = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    parameter_type_registry_getter_candidate = deepattrgetter(
                        "_get_parameter_type_registry",
                        default=None,
                    )(step_definition.parser)[0]

                    if parameter_type_registry_getter_candidate is None:
                        continue

                    parameter_type_registry_getter = cast(
                        "Callable[[FixtureRequest], ParameterTypeRegistry]",
                        parameter_type_registry_getter_candidate,
                    )
                    parameter_type_registry = parameter_type_registry_getter(request)
                    parameter_types = {
                        id(parameter_type): parameter_type for parameter_type in parameter_type_registry.parameter_types
                    }
                    not_yet_registered_parameter_types = {
                        key: parameter_type
                        for key, parameter_type in parameter_types.items()
                        if key not in self.reporter.parameter_type_registry
                    }

                    for parameter_type in not_yet_registered_parameter_types.values():
                        parameter_type_source_reference = _build_parameter_type_source_reference(
                            config,
                            parameter_type,
                        )
                        self.lifecycle_service._emit_envelope(  # noqa: SLF001  -- suppressed warning
                            config,
                            Message(
                                parameter_type=ParameterType(
                                    name=parameter_type.name,
                                    regular_expressions=parameter_type.regexps,
                                    prefer_for_regular_expression_match=parameter_type._prefer_for_regexp_match,  # noqa: SLF001  -- suppressed warning
                                    use_for_snippets=parameter_type._use_for_snippets,  # noqa: SLF001  -- suppressed warning
                                    id=next(IdGenerator.from_stash(config.stash)),
                                    **(
                                        {"source_reference": parameter_type_source_reference}
                                        if parameter_type_source_reference is not None
                                        else {}
                                    ),
                                ),
                            ),
                        )
                    self.reporter.parameter_type_registry |= not_yet_registered_parameter_types.keys()
            step_registry = step_registry.parent
