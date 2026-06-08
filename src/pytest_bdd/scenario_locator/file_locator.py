"""
Provide the file-based scenario locator.

Responsibility:
    Provide the file-based scenario locator. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.scenario_locator.file_locator` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - FileScenarioLocatorDefaults: owns nested behavior below this boundary
    - FileScenarioLocator: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/feature_locator.py: imports or references `file_locator`
    - src/pytest_bdd/scenario_locator/facade.py: imports or references `file_locator`

State and side effects:
    mutates parser_type, media_type, encoding, parse_args, parsed; depends on __future__.annotations, os, enum.Enum,
    operator.methodcaller, pathlib.Path.

Invariants:
    - `pytest_bdd.scenario_locator.file_locator` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises re-raise; callers must treat these as boundary failures.

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

from __future__ import annotations

import os
from enum import Enum
from operator import methodcaller
from pathlib import Path
from typing import TYPE_CHECKING, cast

from attrs import define, field
from cucumber_messages import Source

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pathlib import GlobError
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.util.other import IdGenerator

from .base import ScenarioLocatorFilterMixin

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.mimetype import Mimetype
    from pytest_bdd.types.protocol import HasPytestStash


class FileScenarioLocatorDefaults:
    """
    Provide default values for file scenario locators.

    Responsibility:
        Provide default values for file scenario locators. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.file_locator.FileScenarioLocatorDefaults`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - encoding: owns nested behavior below this boundary
        - parse_args: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `FileScenarioLocatorDefaults`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `FileScenarioLocatorDefaults`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.scenario_locator.file_locator.FileScenarioLocatorDefaults` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    @staticmethod
    def encoding() -> str:
        """
        Return default encoding for feature files.

        Returns:
            Default encoding (utf-8).

        Responsibility:
            Return default encoding for feature files. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocatorDefaults.encoding` because it keeps the nearest
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
            - src/pytest_bdd/feature_locator.py: imports or references `encoding`
            - src/pytest_bdd/parser.py: imports or references `encoding`
            - src/pytest_bdd/plugin/gherkin_message_reporter/stream_relay.py: imports or references `encoding`
            - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `encoding`
            - src/pytest_bdd/scenario.py: imports or references `encoding`

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
        return "utf-8"

    @staticmethod
    def parse_args() -> Args:
        """
        Return default parse arguments.

        Returns:
            Default args tuple.

        Responsibility:
            Return default parse arguments. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocatorDefaults.parse_args` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Args: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `parse_args`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `parse_args`
            - src/pytest_bdd/scenario.py: imports or references `parse_args`
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `parse_args`
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `parse_args`

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
        return Args((), {})


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Represent file scenario locator state.

    Yields:
        Generated values.

    Responsibility:
        Represent file scenario locator state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _try_get_cached_feature: owns nested behavior below this boundary
        - _resolved_feature_paths: owns nested behavior below this boundary
        - resolve_features: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `FileScenarioLocator`
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `FileScenarioLocator`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `FileScenarioLocator`

    State and side effects:
        mutates parser_type, media_type, encoding, parse_args, parsed; depends on returns.maybe.Nothing,
        pytest_bdd.const.PytestConfigParam.

    Invariants:
        - `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

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

    Defaults = FileScenarioLocatorDefaults
    features_base_dir: Path = field()
    feature_paths: list[str | Path] = field(factory=list)
    encoding: str | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    @staticmethod
    def _try_get_cached_feature(
        config: Config | HasPytestStash,
        feature_path: Path,
        uri: str,
        encoding: str,
        media_type: str | None,
    ) -> tuple[ParsedFeature, Source] | None:
        """
        Return (ParsedFeature, Source) from batch parser cache, or None.

        Returns:
            A tuple of (ParsedFeature, Source) if the feature is cached, or None.

        Responsibility:
            Return (ParsedFeature, Source) from batch parser cache, or None. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._try_get_cached_feature` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Nothing.value_or: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - FeatureBatchParser.find_in_stash.value_or: collaborator call used by this boundary
            - FeatureBatchParser.find_in_stash: collaborator call used by this boundary
            - batch_parser.get: collaborator call used by this boundary
            - feature_path.read_text: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_try_get_cached_feature`

        State and side effects:
            mutates batch_parser, cached_doc, cached_doc.uri, raw_data, parsed; depends on returns.maybe.Nothing.

        Invariants:
            - `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._try_get_cached_feature` keeps its
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
            #arch-eval:locational_stability=3

        """
        from returns.maybe import Nothing  # noqa: PLC0415

        batch_parser = FeatureBatchParser.find_in_stash(config.stash).value_or(None)
        if batch_parser is None or not batch_parser.is_flushed:
            return Nothing.value_or(None)
        cached_doc = batch_parser.get(feature_path)
        if cached_doc is None:
            return Nothing.value_or(None)
        cached_doc.uri = uri  # mypy union attribute narrowing
        raw_data = feature_path.read_text(encoding=encoding)
        parsed = ParsedFeature(
            gherkin_document=cached_doc,
            filename=str(feature_path.as_posix()),
            raw_data=raw_data,
        )
        source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
        return parsed, Source(uri=uri, data=parsed.raw_data, media_type=source_media_type)

    @property
    def _resolved_feature_paths(self) -> Iterator[Path]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._resolved_feature_paths` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._resolved_feature_paths` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - sorted: collaborator call used by this boundary
            - filter: collaborator call used by this boundary
            - methodcaller: collaborator call used by this boundary
            - self.features_base_dir.glob: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - feature_path.is_dir: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_resolved_feature_paths`

        State and side effects:
            mutates feature_path.

        Invariants:
            - `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._resolved_feature_paths` keeps its
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
            #arch-eval:locational_stability=3
        """
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = self.features_base_dir / feature_pathlike
                if feature_path.is_dir():
                    yield from sorted(filter(methodcaller("is_file"), feature_path.glob("**/*")))
                else:
                    yield feature_path
            else:
                try:
                    yield from sorted(
                        filter(
                            methodcaller("is_file"),
                            self.features_base_dir.glob(os.fspath(feature_pathlike)),
                        ),
                    )
                except GlobError:
                    yield from sorted(filter(methodcaller("is_file"), self.features_base_dir.glob("**/*")))

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Resolve features.

        Yields:
            Generated values.

        Raises:
            FeatureParseError: If a configured feature cannot be parsed.

        Responsibility:
            Resolve features. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator.resolve_features` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - set: collaborator call used by this boundary
            - already_resolved_feature_paths.add: collaborator call used by this boundary
            - hook_handler.pytest_bdd_get_mimetype: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/base.py: imports or references `resolve_features`
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `resolve_features`

        State and side effects:
            mutates media_type, parser_type, already_resolved_feature_paths, feature_path_key, hook_handler; depends on
            pytest_bdd.const.PytestConfigParam.

        Invariants:
            - `pytest_bdd.scenario_locator.file_locator.FileScenarioLocator.resolve_features` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises re-raise; callers must treat these as boundary failures.

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
        from pytest_bdd.const import PytestConfigParam  # noqa: PLC0415

        already_resolved_feature_paths: set[str] = set()

        for feature_path in self._resolved_feature_paths:
            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                continue

            already_resolved_feature_paths.add(feature_path_key)

            hook_handler = cast("Config", config).hook
            encoding = self.encoding or "utf-8"

            if self.mimetype is None:
                media_type = hook_handler.pytest_bdd_get_mimetype(config=config, path=feature_path)
            elif isinstance(self.mimetype, (Enum,)):
                media_type = self.mimetype.value
            else:
                media_type = self.mimetype

            if self.parser_type is None:
                parser_type = hook_handler.pytest_bdd_get_parser(
                    config=config,
                    mimetype=media_type,
                )
            else:
                parser_type = self.parser_type

            if parser_type is None:
                break

            parser = parser_type(id_generator=IdGenerator.from_stash(config.stash))
            rel_feature_path = Path(relpath(feature_path, self.features_base_dir))
            uri = "file:" + rel_feature_path.as_posix()

            # Check batch parser cache for pre-parsed document
            cached_result = self._try_get_cached_feature(config, feature_path, uri, encoding, media_type)
            if cached_result is not None:
                yield cached_result
                continue

            try:
                parse_args = self.parse_args or Args((), {})
                parsed = parser.parse(
                    config,
                    feature_path,
                    uri,
                    *parse_args.args,
                    **{"encoding": encoding, **parse_args.kwargs},
                )
            except FeatureParseError:
                if cast("Config", config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                    continue
                else:
                    raise
            source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
            yield parsed, Source(uri=uri, data=parsed.raw_data, media_type=source_media_type)
