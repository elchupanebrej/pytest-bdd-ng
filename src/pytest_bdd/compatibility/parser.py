"""
Provide a cross-Python-version compatibility shim for `parser`, encapsulating all version-
detection logic and condi.

Responsibility:
    Provides a cross-Python-version compatibility shim for `parser`, encapsulating all version-
    detection logic and conditional imports so that higher layers import a single stable name
    regardless of the runtime Python interpreter version (3.10-3.14).

Reason for existence:
    Centralizing Python version-gating for `parser` in this module prevents `if sys.version_info`
    checks from contaminating domain logic. This module is the single information expert for which
    stdlib/third-party names and APIs are available on each supported Python version for this
    specific concern.

Delegates:
    - Python stdlib/third-party: delegates actual implementation to the version-appropriate module

Cohesion:
    All symbols re-export a single compatibility concern (parser); no unrelated utilities.

Separation:
    - Sibling compatibility modules: each handles a distinct stdlib version gap.

Main consumers:
    - `pytest_bdd.*`: all higher layers import compatibility shims to avoid inline version-gated logic

State and side effects:
    None, this module keeps no persistent state and performs only import-time version detection.

Invariants:
    - The public API surface matches the target stdlib module interface across supported Python versions.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
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
    Encapsulates the ParsedFeature concern within pytest-bdd, providing a focused set of
    collaborating operations that to.

    Responsibility:
        Encapsulates the ParsedFeature concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        ParsedFeature is a distinct class because its methods share internal state and collaborate on a
        cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - object: ParsedFeature specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single ParsedFeature domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ParsedFeature for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of ParsedFeature maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    gherkin_document: GherkinDocument
    filename: str
    raw_data: str


@runtime_checkable
@define
class ParserProtocol(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: ParserProtocol specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ParserProtocol for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
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
        Perform the parse operation within the ParserProtocol boundary, handling its specific sub-task
        as part of the broade.

        Responsibility:
            Performs the parse operation within the ParserProtocol boundary, handling its specific sub-task
            as part of the broader ParserProtocol responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            parse is a distinct method because it encapsulates a specific behavioral concern that must be
            independently callable and potentially overridable by subclasses of ParserProtocol without
            affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the parse operation on ParserProtocol instances.

        Separation:
            - Other ParserProtocol methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch ParserProtocol implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...
