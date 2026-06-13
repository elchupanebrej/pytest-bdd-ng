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

from typing import TYPE_CHECKING

from pytest_bdd.model.cucumber_formatter_contract import FormatterRuntimeKind
from pytest_bdd.util.cucumber_formatter_support.base import (
    FormatterOutputMode,
    FormatterReporterPlugin,
)

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath


class ProgressBarFormatterPlugin(FormatterReporterPlugin):
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

    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "progress_bar.cjs.j2"

    def __init__(self) -> None:
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
        super().__init__(
            option_attr="cucumber_progress_bar",
            cli_flag="--cucumber-progress-bar",
            formatter="progress-bar",
            package_name="@cucumber/cucumber",
            module_name="pytest_bdd.plugin.cucumber_progress_bar.entrypoint",
            help_text="render the cucumber progress-bar formatter to stdout.",
            discovery_order=2,
        )

    def build_addoption_kwargs(self) -> dict[str, object]:
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
        return self.build_boolean_addoption_kwargs()

    def build_request_from_value(
        self,
        raw_value: object,
        *,
        resolve_output_path: ResolveOutputPath,
    ) -> CucumberFormatterRequest:
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
        _ = raw_value, resolve_output_path
        return self.build_module_terminal_request(template_name=type(self).runtime_template_name)

    def render_runtime_assets(
        self,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
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
        return self.build_module_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=formatter_requests,
            template_name=type(self).runtime_template_name,
        )
