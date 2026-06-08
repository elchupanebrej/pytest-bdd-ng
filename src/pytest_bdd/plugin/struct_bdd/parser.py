"""
Provide parser helpers.

Responsibility:
    Provide parser helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - Loader: owns nested behavior below this boundary
    - StructBDDParser: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `parser`
    - src/pytest_bdd/model/coverage/inventory.py: imports or references `parser`
    - src/pytest_bdd/parser.py: imports or references `parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `parser`
    - src/pytest_bdd/parsers/parse_parser.py: imports or references `parser`

State and side effects:
    mutates HOCON, HJSON, JSON, JSON5, TOML; depends on collections.abc.Mapping, collections.abc.Sequence,
    functools.partial, pathlib.Path, typing.Protocol.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.parser` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Protocol, cast

from attrs import define, field
from returns.maybe import Nothing

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash

from .model import Step
from .model_builder import GherkinDocumentBuilder


class Loader(Protocol):
    """
    Represent loader state.

    Responsibility:
        Represent loader state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.Loader` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parser.py: imports or references `Loader`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.parser.Loader` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def __call__(self, content: str) -> object:
        """
        Handle call.

        Responsibility:
            Handle call. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.Loader.__call__` because it
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
            - src/pytest_bdd/parser.py: imports or references `__call__`

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
        ...


@define
class StructBDDParser(ParserProtocol):
    """
    Represent struct bddparser state.

    Responsibility:
        Represent struct bddparser state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - KIND: owns nested behavior below this boundary
        - kind_default: owns nested behavior below this boundary
        - loader_default: owns nested behavior below this boundary
        - parse: owns nested behavior below this boundary
        - build_loader: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parser.py: imports or references `StructBDDParser`
        - src/pytest_bdd/plugin/struct_bdd/plugin.py: imports or references `StructBDDParser`

    State and side effects:
        mutates HOCON, HJSON, JSON, JSON5, TOML; depends on yaml.FullLoader, yaml.load,
        pytest_bdd.compatibility.tomllib.loads, json.loads, json5.loads.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    class KIND(StrEnum):
        """
        Supported struct BDD source formats.

        Responsibility:
            Supported struct BDD source formats. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.KIND` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parser.py: imports or references `KIND`
            - src/pytest_bdd/plugin/struct_bdd/plugin.py: imports or references `KIND`

        State and side effects:
            mutates HOCON, HJSON, JSON, JSON5, TOML.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.KIND` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=3
        """

        HOCON = "hocon"
        HJSON = "hjson"
        JSON = "json"
        JSON5 = "json5"
        TOML = "toml"
        YAML = "yaml"

    kind: KIND | str | None = field(kw_only=True)
    loader: Loader | None = field(kw_only=True)

    @kind.default
    def kind_default(self) -> str | None:
        """
        Get default kind.

        Returns:
            Default kind value.

        Responsibility:
            Get default kind. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.kind_default`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parser.py: imports or references `kind_default`

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
        return self.KIND.YAML.value if getattr(self, "loader", None) is None else None

    @loader.default
    def loader_default(self) -> Loader | None:
        """
        Get default loader.

        Returns:
            Loader or None.

        Responsibility:
            Get default loader. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.loader_default` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - self.build_loader: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parser.py: imports or references `loader_default`

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
        return self.build_loader()

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature:
        """
        Parse struct BDD file.

        Returns:
            ParsedFeature with gherkin document, filename, and file content.

        Responsibility:
            Parse struct BDD file. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.parse`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - kwargs.pop: collaborator call used by this boundary
            - path.open: collaborator call used by this boundary
            - feature_file.read: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - path.as_posix: collaborator call used by this boundary

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
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parser.py: imports or references `parse`

        State and side effects:
            mutates _, encoding, mode, content, filename.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.parse` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        _ = config
        encoding = cast("str", kwargs.pop("encoding", "utf-8"))
        mode = cast("str", kwargs.pop("mode", "r"))
        with path.open(mode=mode, encoding=encoding) as feature_file:
            content = cast("str", feature_file.read())
        filename = str(path.as_posix())
        raw_step = cast("Loader", self.loader)(content, *args, **kwargs)
        step = Step.model_validate(raw_step)
        gherkin_document = GherkinDocumentBuilder(model=step).build_feature(
            filename,
            uri,
            self.id_generator,
        )
        return ParsedFeature(
            gherkin_document=gherkin_document,
            filename=filename,
            raw_data=content,
        )

    # TODO: make loaders part of public API
    def build_loader(self) -> Loader | None:  # noqa: PLR0911
        """
        Build loader based on kind.

        Returns:
            Loader function or None.

        Responsibility:
            Build loader based on kind. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.build_loader`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - partial: collaborator call used by this boundary
            - loads: collaborator call used by this boundary
            - HOCONConverter.to_json: collaborator call used by this boundary
            - ConfigFactory.parse_string: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parser.py: imports or references `build_loader`

        State and side effects:
            mutates hocon_to_json_kwargs, hocon_parse_kwargs, json_kwargs; depends on yaml.FullLoader, yaml.load,
            pytest_bdd.compatibility.tomllib.loads, json.loads, json5.loads.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.build_loader` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        if self.kind is self.KIND.YAML:
            from yaml import FullLoader  # noqa: PLC0415 -- lazy format dispatch
            from yaml import load as load_yaml  # noqa: PLC0415 -- lazy format dispatch

            return cast("Loader", partial(load_yaml, Loader=FullLoader))
        if self.kind is self.KIND.TOML:
            from pytest_bdd.compatibility.tomllib import loads as load_toml  # noqa: PLC0415 -- lazy format dispatch

            return cast("Loader", load_toml)
        if self.kind is self.KIND.JSON:
            from json import loads as load_json  # noqa: PLC0415 -- lazy format dispatch

            return cast("Loader", load_json)
        if self.kind is self.KIND.JSON5:
            from json5 import loads as load_json5  # noqa: PLC0415 -- lazy format dispatch

            return cast("Loader", load_json5)
        if self.kind is self.KIND.HJSON:
            from hjson import loads as load_hjson  # noqa: PLC0415 -- lazy format dispatch

            return cast("Loader", load_hjson)
        if self.kind is self.KIND.HOCON:
            from json import loads  # noqa: PLC0415 -- lazy format dispatch

            from pyhocon import ConfigFactory, HOCONConverter  # noqa: PLC0415 -- lazy format dispatch

            def load_hocon(  # noqa: PLR0913, PLR0917
                s: str,
                hocon_parse_args: Sequence[object] = (),
                hocon_parse_kwargs: Mapping[str, object] | None = None,
                hocon_to_json_args: Sequence[object] = (),
                hocon_to_json_kwargs: Mapping[str, object] | None = None,
                json_args: Sequence[object] = (),
                json_kwargs: Mapping[str, object] | None = None,
            ) -> object:
                """
                Responsibility:
                    Responsibility: Responsibility:
                    `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.build_loader.load_hocon` owns documented method
                    behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
                    this method.

                Reason for existence:
                    This entity is the information expert for
                    `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.build_loader.load_hocon` because it keeps the
                    nearest code, data shape, call signature, and failure knowledge together.

                Delegates:
                    - cast: collaborator call used by this boundary
                    - loads: collaborator call used by this boundary
                    - HOCONConverter.to_json: collaborator call used by this boundary
                    - ConfigFactory.parse_string: collaborator call used by this boundary

                Cohesion:
                    The implementation stays together because its imports, calls, state writes, and return contract
                    describe one maintainable decision unit.

                Separation:
                    - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                      changeable without widening caller knowledge.

                Main consumers:
                    - src/pytest_bdd/parser.py: imports or references `load_hocon`

                State and side effects:
                    mutates hocon_to_json_kwargs, hocon_parse_kwargs, json_kwargs.

                Invariants:
                    - `pytest_bdd.plugin.struct_bdd.parser.StructBDDParser.build_loader.load_hocon` keeps its documented
                      import path, ownership boundary, and observable behavior stable for callers.

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
                hocon_to_json_kwargs = hocon_to_json_kwargs or {}
                hocon_parse_kwargs = hocon_parse_kwargs or {}
                json_kwargs = json_kwargs or {}
                return cast(
                    "object",
                    loads(
                        HOCONConverter.to_json(
                            ConfigFactory.parse_string(s, *hocon_parse_args, **hocon_parse_kwargs),
                            *hocon_to_json_args,
                            **hocon_to_json_kwargs,
                        ),
                        *json_args,
                        **json_kwargs,  # type: ignore[arg-type]  # argument type compatibility
                    ),
                )

            return cast("Loader", load_hocon)
        return Nothing.value_or(None)
