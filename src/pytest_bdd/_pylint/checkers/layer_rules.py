"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.layer_rules` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _LayerConfig: owns nested behavior below this boundary
    - LayerRulesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates self._config, layers_toml, parts, best, best_len; depends on __future__.annotations, sys, pathlib.Path,
    typing.TYPE_CHECKING, typing.cast.

Invariants:
    - `pytest_bdd._pylint.checkers.layer_rules` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

# init: allow
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from astroid import nodes
from pylint.checkers import BaseChecker

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]  # fallback for python < 3.11

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class _LayerConfig:
    """
    Loaded layer configuration from layers.toml.

    Responsibility:
        Loaded layer configuration from layers.toml. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.layer_rules._LayerConfig` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - layer_for_module: owns nested behavior below this boundary
        - order_for_layer: owns nested behavior below this boundary
        - allowed_imports_for_layer: owns nested behavior below this boundary
        - is_exception: owns nested behavior below this boundary
        - module_prefixes: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates raw, self._layers, self._exceptions, self._module_to_layer, sorted_modules.

    Invariants:
        - `pytest_bdd._pylint.checkers.layer_rules._LayerConfig` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def __init__(self, layers_toml_path: Path) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.__init__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - tomllib.loads: collaborator call used by this boundary
            - layers_toml_path.read_text: collaborator call used by this boundary
            - set: collaborator call used by this boundary
            - raw.get: collaborator call used by this boundary
            - self._exceptions.add: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`
            - src/pytest_bdd/parsers/base.py: imports or references `__init__`

        State and side effects:
            mutates raw, self._layers, self._exceptions, self._module_to_layer, sorted_modules.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.__init__` keeps its documented import path,
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
            #arch-eval:locational_stability=4
        """
        raw = tomllib.loads(layers_toml_path.read_text(encoding="utf-8"))
        self._layers: dict[str, dict[str, object]] = raw["layers"]
        self._exceptions: set[tuple[str, str]] = set()
        for exc in raw.get("exceptions", []):
            self._exceptions.add((exc["from_module"], exc["to_module"]))
        self._module_to_layer: dict[str, str] = {}
        sorted_modules = sorted(
            ((m, name) for name, ldef in self._layers.items() for m in ldef["modules"]),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for mod_prefix, layer_name in sorted_modules:
            self._module_to_layer[mod_prefix] = layer_name

    def layer_for_module(self, module: str) -> str | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.layer_for_module` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.layer_for_module` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._module_to_layer.items: collaborator call used by this boundary
            - module.startswith: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        for prefix, layer_name in self._module_to_layer.items():
            if module == prefix or module.startswith(prefix + "."):
                return layer_name
        return None

    def order_for_layer(self, layer: str) -> int:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.order_for_layer` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.order_for_layer` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        return cast("int", self._layers[layer]["order"])

    def allowed_imports_for_layer(self, layer: str) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.allowed_imports_for_layer` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.allowed_imports_for_layer` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        return cast("list[str]", self._layers[layer]["allowed_imports"])

    def is_exception(self, from_module: str, to_module: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.is_exception` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.is_exception` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - from_module.startswith: collaborator call used by this boundary
            - to_module.startswith: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        for exc_from, exc_to in self._exceptions:
            if (from_module == exc_from or from_module.startswith(exc_from + ".")) and (
                to_module == exc_to or to_module.startswith(exc_to + ".")
            ):
                return True
        return False

    def module_prefixes(self) -> dict[str, str]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.module_prefixes` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules._LayerConfig.module_prefixes` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

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
        return self._module_to_layer


class LayerRulesChecker(BaseChecker):
    """
    Checker for architectural layer rule enforcement: BLQ1301, BLQ1302.

    Responsibility:
        Checker for architectural layer rule enforcement: BLQ1301, BLQ1302. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _init_config: owns nested behavior below this boundary
        - visit_import: owns nested behavior below this boundary
        - visit_importfrom: owns nested behavior below this boundary
        - _check_node_imports: owns nested behavior below this boundary
        - _check_import: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `LayerRulesChecker`

    State and side effects:
        mutates self._config, layers_toml, parts, best, best_len.

    Invariants:
        - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    name = "layer-rules"

    msgs = {
        "E9041": (
            "BLQ1301: downward import — module %s (layer %s, order %s) imports "
            "%s (layer %s, order %s). Allowed imports: %s.",
            "downward-import",
            "BLQ1301: Downward layer imports are forbidden.",
        ),
        "E9042": (
            "BLQ1302: horizontal import — module %s (layer %s) imports %s from "
            "same layer. Cross-module imports within layer %s are forbidden.",
            "horizontal-import",
            "BLQ1302: Horizontal layer imports are forbidden.",
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker.__init__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker.__init__` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary
            - self._init_config: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`
            - src/pytest_bdd/parsers/base.py: imports or references `__init__`

        State and side effects:
            mutates self._config.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker.__init__` keeps its documented import path,
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
            #arch-eval:locational_stability=4
        """
        super().__init__(linter)
        self._config: _LayerConfig | None = None
        self._init_config()

    def _init_config(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._init_config`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._init_config` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - layers_toml.exists: collaborator call used by this boundary
            - Path.resolve: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - candidate.exists: collaborator call used by this boundary
            - _LayerConfig: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates layers_toml, self._config, current, candidate.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._init_config` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        # Find docs/architecture/layers.toml relative to repository root
        layers_toml = Path("docs/architecture/layers.toml")
        if not layers_toml.exists():
            # Try walking up from current directory to find it
            current = Path().resolve()
            for parent in [current] + list(current.parents):
                candidate = parent / "docs" / "architecture" / "layers.toml"
                if candidate.exists():
                    layers_toml = candidate
                    break

        if layers_toml.exists():
            try:
                self._config = _LayerConfig(layers_toml)
            except Exception:  # noqa: BLE001
                self._config = None

    def visit_import(self, node: nodes.Import) -> None:
        """
        Check direct import statements.

        Responsibility:
            Check direct import statements. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker.visit_import` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node_imports: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node_imports(node)

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Check import-from statements.

        Responsibility:
            Check import-from statements. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker.visit_importfrom` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node_imports: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node_imports(node)

    def _check_node_imports(self, node: nodes.Import | nodes.ImportFrom) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_node_imports` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_node_imports` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._is_pytest_bdd_module: collaborator call used by this boundary
            - node.root: collaborator call used by this boundary
            - self._config.layer_for_module: collaborator call used by this boundary
            - self._resolve_imported_modules: collaborator call used by this boundary
            - self._check_import: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates current_module, current_layer, resolved.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_node_imports` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        if not self._config:
            return

        current_module = node.root().name
        if not current_module or not self._is_pytest_bdd_module(current_module):
            return

        current_layer = self._config.layer_for_module(current_module)
        if not current_layer:
            return

        resolved = self._resolve_imported_modules(node, current_module)
        for imported_module in resolved:
            if not self._is_pytest_bdd_module(imported_module):
                continue
            self._check_import(node, current_module, current_layer, imported_module)

    def _check_import(
        self,
        node: nodes.NodeNG,
        current_module: str,
        current_layer: str,
        imported_module: str,
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_import`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_import` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._resolve_package: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary
            - config.order_for_layer: collaborator call used by this boundary
            - config.layer_for_module: collaborator call used by this boundary
            - current_module.startswith: collaborator call used by this boundary
            - imported_module.startswith: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates config, imported_layer, imported_package, current_package, is_plugin_import.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._check_import` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        config = self._config
        if not config:
            return

        imported_layer = config.layer_for_module(imported_module)
        if not imported_layer:
            return

        imported_package = self._resolve_package(imported_module)
        current_package = self._resolve_package(current_module)

        # BLQ1302: horizontal import (only between different plugins)
        if imported_layer == current_layer:
            is_plugin_import = current_module.startswith("pytest_bdd.plugin.") and imported_module.startswith(
                "pytest_bdd.plugin."
            )
            if is_plugin_import and imported_package != current_package:
                self.add_message(
                    "horizontal-import",
                    node=node,
                    args=(current_module, current_layer, imported_module, imported_layer),
                )
            return

        # If they are in the same package (e.g. submodules), it's allowed
        if imported_package is not None and imported_package == current_package:
            return

        # Check allowed imports
        allowed = config.allowed_imports_for_layer(current_layer)
        if imported_layer in allowed:
            return

        # Check orders
        imported_order = config.order_for_layer(imported_layer)
        current_order = config.order_for_layer(current_layer)

        if imported_order >= current_order:
            if config.is_exception(current_module, imported_module):
                return
            allowed_str = ", ".join(allowed) if allowed else "none"
            self.add_message(
                "downward-import",
                node=node,
                args=(
                    current_module,
                    current_layer,
                    current_order,
                    imported_module,
                    imported_layer,
                    imported_order,
                    allowed_str,
                ),
            )

    def _resolve_package(self, module: str) -> str | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_package`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_package` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - module.split: collaborator call used by this boundary
            - self._config.module_prefixes: collaborator call used by this boundary
            - candidate.split: collaborator call used by this boundary
            - enumerate: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates best, best_len, match, parts, candidate_parts.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_package` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        if not self._config:
            return None
        parts = module.split(".")
        best: str | None = None
        best_len = 0
        for candidate in self._config.module_prefixes():
            candidate_parts = candidate.split(".")
            if len(candidate_parts) <= len(parts):
                match = True
                for i, cp in enumerate(candidate_parts):
                    if parts[i] != cp:
                        match = False
                        break
                if match and len(candidate_parts) > best_len:
                    best = candidate
                    best_len = len(candidate_parts)
        return best

    def _is_pytest_bdd_module(self, module: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._is_pytest_bdd_module` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._is_pytest_bdd_module` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - module.startswith: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        return module == "pytest_bdd" or module.startswith("pytest_bdd.")

    def _resolve_imported_modules(
        self,
        node: nodes.Import | nodes.ImportFrom,
        current_file_module: str,
    ) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_imported_modules` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_imported_modules` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - current_file_module.split: collaborator call used by this boundary
            - range: collaborator call used by this boundary
            - parts.pop: collaborator call used by this boundary
            - parts.append: collaborator call used by this boundary
            - join: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates module, parts.

        Invariants:
            - `pytest_bdd._pylint.checkers.layer_rules.LayerRulesChecker._resolve_imported_modules` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        if isinstance(node, nodes.ImportFrom):
            if node.modname is None:
                return []
            module = node.modname
            if node.level and node.level > 0:
                parts = current_file_module.split(".")
                for _ in range(node.level - (1 if module else 0)):
                    if parts:
                        parts.pop()
                if module:
                    parts.append(module)
                module = ".".join(parts)
            return [module]
        return [alias[0] for alias in node.names]
