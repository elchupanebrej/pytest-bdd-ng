"""
Provide service base helpers.

Responsibility:
    Provide service base helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.service_base` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ReporterServiceBase: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `service_base`
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `service_base`
    - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `service_base`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `service_base`
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references `service_base`

State and side effects:
    mutates plugin_suffix, reporter, message; depends on __future__.annotations, typing.TYPE_CHECKING, typing.ClassVar,
    attrs.define, attrs.field.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.service_base` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


@define(eq=False)
class ReporterServiceBase:
    """
    Represent reporter service base state.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Represent reporter service base state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.service_base.ReporterServiceBase` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - plugin_name: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
          `ReporterServiceBase`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `ReporterServiceBase`
        - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
          `ReporterServiceBase`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ReporterServiceBase`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `ReporterServiceBase`

    State and side effects:
        mutates plugin_suffix, reporter, message.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.service_base.ReporterServiceBase` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

    """

    plugin_suffix: ClassVar[str | None] = None
    reporter: GherkinMessageReporter = field()

    @property
    def plugin_name(self) -> str:
        """
        Handle plugin name.

        Raises:
            ValueError: If the operation cannot be completed.

        Responsibility:
            Handle plugin name. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.service_base.ReporterServiceBase.plugin_name` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `plugin_name`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `plugin_name`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `plugin_name`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `plugin_name`

        State and side effects:
            mutates plugin_suffix, message.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.service_base.ReporterServiceBase.plugin_name` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        plugin_suffix = type(self).plugin_suffix
        if plugin_suffix is None:
            message = f"{type(self).__name__} does not define plugin_suffix"
            raise ValueError(message)
        return f"{type(self.reporter).plugin_name}:{plugin_suffix}"
