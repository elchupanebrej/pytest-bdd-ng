"""
Provide collector helpers.

Responsibility:
    Provide collector helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.collector` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - Module: owns nested behavior below this boundary
    - FeatureFileModule: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `collector`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `collector`

State and side effects:
    mutates features_path_type, feature_pathlike, base_dir, path, config_parser; depends on logging,
    collections.abc.Iterable, configparser.ConfigParser, importlib.machinery.ModuleSpec,
    importlib.util.module_from_spec.

Invariants:
    - `pytest_bdd.collector` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

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

import logging
from collections.abc import Iterable
from configparser import ConfigParser
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from types import ModuleType
from typing import cast
from urllib.parse import urlparse
from uuid import uuid4

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.pytest import Collector, Item
from pytest_bdd.compatibility.pytest import Module as PytestModule
from pytest_bdd.scenario import FeaturePathType as PathType
from pytest_bdd.scenario import scenarios
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.other import format_as_python_identifier
from pytest_bdd.util.webloc import read as webloc_read

logger = logging.getLogger(__name__)


class Module(PytestModule):
    """
    Represent module state.

    Responsibility:
        Represent module state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector.Module` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - collect: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/init_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `Module`
        - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `Module`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.collector.Module` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

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

    def collect(self) -> Iterable[Item | Collector]:
        """
        Collect tests from this module.

        Returns:
            Iterable of pytest items and collectors.

        Responsibility:
            Collect tests from this module. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector.Module.collect` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - StepDefinitionManager.Registry.inject_registry_fixture: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - super.collect: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `collect`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `collect`

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
        StepDefinitionManager.Registry.inject_registry_fixture(self.obj)
        return cast("Iterable[Item | Collector]", super().collect())  # type: ignore[misc]  # pytest Module.collect is untyped


class FeatureFileModule(Module):
    """
    Represent feature file module state.

    Responsibility:
        Represent feature file module state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector.FeatureFileModule` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - collect: owns nested behavior below this boundary
        - _getobj: owns nested behavior below this boundary
        - _build_test_module: owns nested behavior below this boundary
        - detect_uri_pathtype: owns nested behavior below this boundary
        - get_feature_pathlike_from_url_file: owns nested behavior below this boundary
        - get_feature_pathlike_from_desktop_file: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `FeatureFileModule`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `FeatureFileModule`

    State and side effects:
        mutates features_path_type, feature_pathlike, base_dir, path, config_parser.

    Invariants:
        - `pytest_bdd.collector.FeatureFileModule` keeps its documented import path, ownership boundary, and observable
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
        #arch-eval:locational_stability=3
    """

    def collect(self) -> Iterable[Item | Collector]:
        """
        Collect tests, flushing the batch parser if pending.

        Returns:
            Iterable of pytest items and collectors.

        Responsibility:
            Collect tests, flushing the batch parser if pending. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector.FeatureFileModule.collect` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - FeatureBatchParser.find_in_stash.value_or: collaborator call used by this boundary
            - FeatureBatchParser.find_in_stash: collaborator call used by this boundary
            - batch_parser.has_pending: collaborator call used by this boundary
            - batch_parser.flush: collaborator call used by this boundary
            - super.collect: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `collect`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `collect`

        State and side effects:
            mutates batch_parser.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule.collect` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        batch_parser = FeatureBatchParser.find_in_stash(self.config.stash).value_or(None)
        if batch_parser is not None and batch_parser.has_pending():
            batch_parser.flush()
        return super().collect()

    def _getobj(self) -> ModuleType:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.collector.FeatureFileModule._getobj` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector.FeatureFileModule._getobj` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.get_path: collaborator call used by this boundary
            - self.get_feature_pathlike_from_url_file: collaborator call used by this boundary
            - self.get_feature_pathlike_from_desktop_file: collaborator call used by this boundary
            - self.get_feature_pathlike_from_weblock_file: collaborator call used by this boundary
            - self._build_test_module: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_getobj`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_getobj`

        State and side effects:
            mutates feature_pathlike, features_path_type, base_dir, path.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule._getobj` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        path: Path = self.get_path()
        feature_pathlike: str | Path | None
        features_path_type: PathType
        base_dir: str | Path | None
        if path.suffixes[-1] == ".url":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_url_file(path)
        elif path.suffixes[-1] == ".desktop":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_desktop_file(path)
        elif path.suffixes[-1] == ".webloc":
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_weblock_file(path)
        else:
            feature_pathlike, features_path_type, base_dir = path, PathType.PATH, None
        return self._build_test_module(feature_pathlike, features_path_type, base_dir)

    def _build_test_module(
        self,
        path: Path | str | None,
        features_path_type: PathType,
        base_dir: Path | str | None,
    ) -> ModuleType:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.collector.FeatureFileModule._build_test_module` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector.FeatureFileModule._build_test_module`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - format_as_python_identifier: collaborator call used by this boundary
            - uuid4: collaborator call used by this boundary
            - ModuleSpec: collaborator call used by this boundary
            - module_from_spec: collaborator call used by this boundary
            - scenarios: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_build_test_module`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_build_test_module`

        State and side effects:
            mutates module_name, module_spec, module, module.test_scenarios.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule._build_test_module` keeps its documented import path, ownership
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
            #arch-eval:locational_stability=3
        """
        module_name = format_as_python_identifier(f"{path}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = module_from_spec(module_spec)

        module.test_scenarios = scenarios(  # type:ignore[attr-defined]  # upstream type stubs missing this attribute
            *((path,) if path is not None else []),
            filter_=None,
            return_test_decorator=False,
            parser_type=getattr(self, "parser_type", None),
            features_base_dir=base_dir,
            features_path_type=features_path_type,
        )

        return module

    @staticmethod
    def detect_uri_pathtype(path: str | None) -> tuple[str | None, PathType]:
        """
        Detect URI path type from a URL string.

        Args:
            path: URL string to parse.

        Returns:
            Tuple of (parsed_path, path_type).

        Responsibility:
            Detect URI path type from a URL string. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector.FeatureFileModule.detect_uri_pathtype`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - urlparse: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `detect_uri_pathtype`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `detect_uri_pathtype`

        State and side effects:
            mutates features_path_type, parsed_url, path.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule.detect_uri_pathtype` keeps its documented import path, ownership
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
            #arch-eval:locational_stability=3

        """
        try:
            parsed_url = urlparse(path)
        except ValueError:
            features_path_type = PathType.UNDEFINED
        else:
            if parsed_url.scheme == "file":
                features_path_type = PathType.PATH
                path = str(parsed_url.path)
            elif parsed_url.scheme:
                features_path_type = PathType.URL
            else:
                features_path_type = PathType.UNDEFINED
        return path, features_path_type

    @classmethod
    def get_feature_pathlike_from_url_file(cls, path: Path) -> tuple[str | None, PathType, str | None]:
        """
        Get feature path from a .url file.

        Args:
            path: Path to the .url file.

        Returns:
            Tuple of (feature_path, path_type, working_dir).

        Responsibility:
            Get feature path from a .url file. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.collector.FeatureFileModule.get_feature_pathlike_from_url_file` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - config_data.get: collaborator call used by this boundary
            - ConfigParser: collaborator call used by this boundary
            - config_parser.read: collaborator call used by this boundary
            - cls.detect_uri_pathtype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `get_feature_pathlike_from_url_file`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `get_feature_pathlike_from_url_file`

        State and side effects:
            mutates config_parser, config_data, working_dir, url.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule.get_feature_pathlike_from_url_file` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["InternetShortcut"]
        working_dir = config_data.get("WorkingDirectory", None)
        url = config_data.get("URL", None)
        return *cls.detect_uri_pathtype(url), working_dir

    @classmethod
    def get_feature_pathlike_from_desktop_file(cls, path: Path) -> tuple[str | None, PathType, None]:
        """
        Get feature path from a .desktop file.

        Args:
            path: Path to the .desktop file.

        Returns:
            Tuple of (feature_path, path_type, None).

        Responsibility:
            Get feature path from a .desktop file. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.collector.FeatureFileModule.get_feature_pathlike_from_desktop_file` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ConfigParser: collaborator call used by this boundary
            - config_parser.read: collaborator call used by this boundary
            - cls.detect_uri_pathtype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `get_feature_pathlike_from_desktop_file`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `get_feature_pathlike_from_desktop_file`

        State and side effects:
            mutates config_parser, config_data.

        Invariants:
            - `pytest_bdd.collector.FeatureFileModule.get_feature_pathlike_from_desktop_file` keeps its documented
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
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["Desktop Entry"]
        return *cls.detect_uri_pathtype(config_data["URL"] if config_data["Type"] == "Link" else None), None

    @classmethod
    def get_feature_pathlike_from_weblock_file(cls, path: Path) -> tuple[str | None, PathType, None]:
        """
        Get feature path from a .webloc file.

        Args:
            path: Path to the .webloc file.

        Returns:
            Tuple of (feature_path, path_type, None).

        Responsibility:
            Get feature path from a .webloc file. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.collector.FeatureFileModule.get_feature_pathlike_from_weblock_file` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.detect_uri_pathtype: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - webloc_read: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `get_feature_pathlike_from_weblock_file`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `get_feature_pathlike_from_weblock_file`

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
        return *cls.detect_uri_pathtype(cast("str", webloc_read(str(path)))), None
