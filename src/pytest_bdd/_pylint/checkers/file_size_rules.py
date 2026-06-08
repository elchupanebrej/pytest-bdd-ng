"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.file_size_rules` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.file_size_rules` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - FileSizeRulesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates count, _MAX_LOC, _MIN_CLUSTERS_TO_REPORT, name, msgs; depends on __future__.annotations,
    collections.defaultdict, pathlib.Path, astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.file_size_rules` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
"""

# init: allow
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

_MAX_LOC = 400
_MIN_CLUSTERS_TO_REPORT = 3


class FileSizeRulesChecker(BaseChecker):
    """
    Checker for file size and decomposition: BLQ1201, BLQ1202.

    Responsibility:
        Checker for file size and decomposition: BLQ1201, BLQ1202. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - visit_module: owns nested behavior below this boundary
        - _count_logical_lines: owns nested behavior below this boundary
        - _check_clusters: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `FileSizeRulesChecker`

    State and side effects:
        mutates count, name, msgs, filepath, path.

    Invariants:
        - `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker` keeps its documented import path, ownership
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

    name = "file-size-rules"

    msgs = {
        "R9031": (
            "BLQ1201: file has %s lines of code (max %s). Consider splitting into a package.",
            "file-too-long",
            "BLQ1201: Files exceeding 400 logical lines of code are forbidden.",
        ),
        "R9032": (
            "BLQ1202: file has %s responsibility clusters. Suggested split: %s",
            "multiple-responsibility-clusters",
            "BLQ1202: Files with multiple responsibility clusters are forbidden.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Analyze module for logical line count and responsibility clusters.

        Responsibility:
            Analyze module for logical line count and responsibility clusters. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker.visit_module` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - path.read_text: collaborator call used by this boundary
            - self._count_logical_lines: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary
            - self._check_clusters: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath, path, source, loc.

        Invariants:
            - `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker.visit_module` keeps its documented
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
        filepath = node.file
        if not filepath:
            return

        # Skip testing packages
        if "pytest_bdd_testing" in filepath:
            return

        path = Path(filepath)

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Check BLQ1201: logical lines count
        loc = self._count_logical_lines(source)
        if loc > _MAX_LOC:
            self.add_message("file-too-long", node=node, args=(loc, _MAX_LOC))

        # Check BLQ1202: responsibility clusters
        self._check_clusters(node, path)

    def _count_logical_lines(self, source: str) -> int:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._count_logical_lines` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._count_logical_lines` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - source.splitlines: collaborator call used by this boundary
            - raw_line.strip: collaborator call used by this boundary
            - stripped.startswith: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates count, stripped.

        Invariants:
            - `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._count_logical_lines` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        count = 0
        for raw_line in source.splitlines():
            stripped = raw_line.strip()
            if stripped and not stripped.startswith("#"):
                count += 1
        return count

    def _check_clusters(self, node: nodes.Module, path: Path) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._check_clusters` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._check_clusters` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - defaultdict: collaborator call used by this boundary
            - child.nodes_of_class: collaborator call used by this boundary
            - frozenset: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates module_level_names, clusters, used_names, shared, key.

        Invariants:
            - `pytest_bdd._pylint.checkers.file_size_rules.FileSizeRulesChecker._check_clusters` keeps its documented
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
        # Get module level names
        module_level_names = {
            child.name
            for child in node.body
            if isinstance(child, (nodes.ClassDef, nodes.FunctionDef, nodes.AsyncFunctionDef))
        }

        # Build clusters
        clusters: dict[frozenset[str], list[str]] = defaultdict(list)
        for child in node.body:
            if isinstance(child, (nodes.ClassDef, nodes.FunctionDef, nodes.AsyncFunctionDef)):
                # Collect all Name nodes in child
                used_names = {desc.name for desc in child.nodes_of_class(nodes.Name)}

                shared = used_names & module_level_names
                if shared:
                    key = frozenset(shared)
                    clusters[key].append(child.name)

        reportable = [c for c in clusters.values() if len(c) > 1]

        if len(reportable) >= _MIN_CLUSTERS_TO_REPORT:
            cluster_descriptions = []
            for i, members in enumerate(reportable, start=1):
                cluster_descriptions.append(
                    f"cluster '{chr(64 + i)}' ({', '.join(sorted(members))})",
                )
            suggestion = "; ".join(cluster_descriptions)
            self.add_message(
                "multiple-responsibility-clusters",
                node=node,
                args=(len(reportable), suggestion),
            )
