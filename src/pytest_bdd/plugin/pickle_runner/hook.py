"""
Provide hook helpers.

Responsibility:
    Provide hook helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.hook` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - PickleRunnerHookSpec: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/hook.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `hook`

State and side effects:
    depends on collections.deque, collections.abc.Callable, pytest, cucumber_messages.PickleStep,
    pytest_bdd.compatibility.pytest.FixtureRequest.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.hook` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from collections import deque
from collections.abc import Callable

import pytest
from cucumber_messages import PickleStep as Step

from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.model.run import Run
from pytest_bdd.steps import Definition, StepFunc


class PickleRunnerHookSpec:
    """
    Represent pickle runner hook spec state.

    Responsibility:
        Represent pickle runner hook spec state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_before_scenario: owns nested behavior below this boundary
        - pytest_bdd_run_scenario: owns nested behavior below this boundary
        - pytest_bdd_after_scenario: owns nested behavior below this boundary
        - pytest_bdd_run_step: owns nested behavior below this boundary
        - pytest_bdd_before_step: owns nested behavior below this boundary
        - pytest_bdd_before_step_call: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `PickleRunnerHookSpec`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `PickleRunnerHookSpec`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def pytest_bdd_before_scenario(self, request: FixtureRequest, run: Run) -> None:
        """
        Call before scenario is executed.

        Responsibility:
            Call before scenario is executed. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_before_scenario` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_run_scenario(self, request: FixtureRequest, run: Run) -> object:
        """
        Execute scenario protocol.

        Responsibility:
            Execute scenario protocol. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_run_scenario` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_after_scenario(self, request: FixtureRequest, run: Run) -> None:
        """
        Call after scenario is executed.

        Responsibility:
            Call after scenario is executed. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_after_scenario` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_run_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """
        Execute run step protocol.

        Responsibility:
            Execute run step protocol. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_run_step` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
    ) -> None:
        """
        Call before step function is set up.

        Responsibility:
            Call before step function is set up. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_before_step` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_before_step_call(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: Definition,
    ) -> None:
        """
        Call before step function is executed.

        Responsibility:
            Call before step function is executed. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_before_step_call` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: Definition,
    ) -> None:
        """
        Call after step function is successfully executed.

        Responsibility:
            Call after step function is successfully executed. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_after_step` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_step_error(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        exception: Exception,
        step_definition: Definition,
    ) -> None:
        """
        Call when step function failed to execute.

        Responsibility:
            Call when step function failed to execute. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_step_error` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def pytest_bdd_step_func_lookup_error(
        self,
        request: FixtureRequest,
        run: Run,
        exception: Exception,
    ) -> None:
        """
        Call when step lookup failed.

        Responsibility:
            Call when step lookup failed. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_step_func_lookup_error` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_match_step_definition_to_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> Definition | None:
        """
        Find match between scenario step and user defined step function.

        Responsibility:
            Find match between scenario step and user defined step function. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_match_step_definition_to_step` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references
              `pytest_bdd_match_step_definition_to_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `pytest_bdd_match_step_definition_to_step`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `pytest_bdd_match_step_definition_to_step`

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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_caller(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: Definition,
    ) -> Callable[[], object] | None:
        """
        Provide alternative approach to execute step.

        Responsibility:
            Provide alternative approach to execute step. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_get_step_caller` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `pytest_bdd_get_step_caller`

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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> Callable[[deque[Step]], object] | None:
        """
        Provide alternative approach to execute scenario steps.

        Responsibility:
            Provide alternative approach to execute scenario steps. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_get_step_dispatcher` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references
              `pytest_bdd_get_step_dispatcher`

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

    def pytest_bdd_attach(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        attachment: object,
        media_type: str | None,
        file_name: str | None,
        source_data: str | None,
        source_media_type: str | None,
        source_uri: str | None,
        url: str | None,
        as_external: bool,  # noqa: FBT001
        test_run_hook_started_id: str | None,
        test_run_started_id: str | None,
    ) -> None:
        """
        Add attachment to a test case from an internal hook.

        Responsibility:
            Add attachment to a test case from an internal hook. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.hook.PickleRunnerHookSpec.pytest_bdd_attach` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `pytest_bdd_attach`

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
            #arch-eval:locational_stability=3
        """
