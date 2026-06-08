"""
Provide parser helpers.

Responsibility:
    Provide parser helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.parser` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - ParsedFeature: owns nested behavior below this boundary
    - ParserProtocol: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `parser`
    - src/pytest_bdd/feature_locator.py: imports or references `parser`
    - src/pytest_bdd/model/coverage/inventory.py: imports or references `parser`
    - src/pytest_bdd/parser.py: imports or references `parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `parser`

State and side effects:
    mutates gherkin_document, filename, raw_data, id_generator; depends on pathlib.Path, typing.Protocol,
    typing.runtime_checkable, attrs.define, attrs.field.

Invariants:
    - `pytest_bdd.compatibility.parser` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from attrs import define, field
from cucumber_messages import (
    GherkinDocument,  # upstream library missing type stubs
)

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator


@define
class ParsedFeature:
    """
    Parsed feature result — bundles gherkin document, filename, and raw source data.

    Responsibility:
        Parsed feature result — bundles gherkin document, filename, and raw source data. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.parser.ParsedFeature` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `ParsedFeature`
        - src/pytest_bdd/parser.py: imports or references `ParsedFeature`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `ParsedFeature`
        - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `ParsedFeature`
        - src/pytest_bdd/scenario.py: imports or references `ParsedFeature`

    State and side effects:
        mutates gherkin_document, filename, raw_data.

    Invariants:
        - `pytest_bdd.compatibility.parser.ParsedFeature` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    gherkin_document: GherkinDocument
    filename: str
    raw_data: str


@runtime_checkable
@define
class ParserProtocol(Protocol):
    """
    Define the parser protocol contract.

    Responsibility:
        Define the parser protocol contract. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.parser.ParserProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `ParserProtocol`
        - src/pytest_bdd/parser.py: imports or references `ParserProtocol`
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `ParserProtocol`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `ParserProtocol`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `ParserProtocol`

    State and side effects:
        mutates id_generator.

    Invariants:
        - `pytest_bdd.compatibility.parser.ParserProtocol` keeps its documented import path, ownership boundary, and
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

    id_generator: IdGenerator | None = field(default=None, kw_only=True)

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature:  # pragma: no cover
        """
        Parse parse.

        Responsibility:
            Parse parse. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.compatibility.parser.ParserProtocol.parse` because it
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
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/feature_locator.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`

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
        ...
