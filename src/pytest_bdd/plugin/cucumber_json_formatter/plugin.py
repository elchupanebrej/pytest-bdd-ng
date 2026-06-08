"""
Provide cucumber json formatter helpers.

Responsibility:
    Provide cucumber json formatter helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json_formatter.plugin` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - JsonFormatterPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `plugin`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `plugin`

State and side effects:
    mutates output_mode; depends on __future__.annotations, typing.TYPE_CHECKING,
    pytest_bdd.util.cucumber_formatter_support.base.FormatterOutputMode,
    pytest_bdd.util.cucumber_formatter_support.base.FormatterReporterPlugin,
    pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRequest.

Invariants:
    - `pytest_bdd.plugin.cucumber_json_formatter.plugin` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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

from typing import TYPE_CHECKING

from pytest_bdd.util.cucumber_formatter_support.base import FormatterOutputMode, FormatterReporterPlugin

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath


class JsonFormatterPlugin(FormatterReporterPlugin):
    """
    Represent json formatter plugin state.

    Responsibility:
        Represent json formatter plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json_formatter.plugin.JsonFormatterPlugin`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - build_addoption_kwargs: owns nested behavior below this boundary
        - build_request_from_value: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json_formatter/entrypoint.py: imports or references `JsonFormatterPlugin`

    State and side effects:
        mutates output_mode.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json_formatter.plugin.JsonFormatterPlugin` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    output_mode = FormatterOutputMode.path

    def __init__(self) -> None:
        """
        Initialize the json formatter plugin.

        Responsibility:
            Initialize the json formatter plugin. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json_formatter.plugin.JsonFormatterPlugin.__init__` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

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
        super().__init__(
            option_attr="cucumber_js_json_path",
            cli_flag="--cucumber-json",
            formatter="json",
            package_name="@cucumber/cucumber",
            module_name="pytest_bdd.plugin.cucumber_json_formatter.entrypoint",
            help_text="render the cucumber json formatter to the given path.",
            discovery_order=3,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
        """
        Build addoption kwargs.

        Returns:
            Keyword arguments for addoption.

        Responsibility:
            Build addoption kwargs. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json_formatter.plugin.JsonFormatterPlugin.build_addoption_kwargs` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.build_required_path_addoption_kwargs: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/util/cucumber_formatter_support/base.py: imports or references `build_addoption_kwargs`
            - src/pytest_bdd/util/cucumber_formatters.py: imports or references `build_addoption_kwargs`

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
        return self.build_required_path_addoption_kwargs()

    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
        """
        Build request from value.

        Returns:
            Cucumber formatter request.

        Responsibility:
            Build request from value. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json_formatter.plugin.JsonFormatterPlugin.build_request_from_value` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.build_builtin_required_path_request: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/util/cucumber_formatter_support/base.py: imports or references `build_request_from_value`

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
        return self.build_builtin_required_path_request(raw_value, resolve_output_path=resolve_output_path)
