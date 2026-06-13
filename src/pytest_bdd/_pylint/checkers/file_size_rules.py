"""
Enforces file-level size and complexity limits on the pytest-bdd-ng codebase.

Responsibility:
    Enforces file-level size and complexity limits on the pytest-bdd-ng codebase. Validates two rules:
    BLQ1201 (file-too-long) fires when a module exceeds 1200 logical lines of code (non-blank, non-comment),
    and BLQ1202 (multiple-responsibility-clusters) fires when a module has 3 or more distinct responsibility
    clusters — groups of top-level definitions that share references to common module-level names. Both checks
    run during `visit_module` on every non-test Python file, with the `pytest_bdd_testing` directory and
    unreadable files silently skipped.

Reason for existence:
    This module is the single authority on file size governance for the project. It encapsulates the heuristics
    for counting logical lines (stripping blanks and comments) and for detecting responsibility clusters via
    shared-name analysis of AST nodes. Keeping this separate from other quality checkers prevents the
    QualityGatesChecker from becoming a dumping ground for unrelated rules and allows independent threshold
    tuning (e.g., changing `_MAX_LOC` or `_MIN_CLUSTERS_TO_REPORT`) without affecting other checkers.
    The cluster detection algorithm — collecting `nodes.Name` references within class/function bodies and
    intersecting them with module-level names — is specific enough to warrant its own module.

Delegates:
    - Path.read_text: Delegates file reading to the stdlib for source text retrieval.
    - self._count_logical_lines: Counts non-blank, non-comment lines in source text for BLQ1201.
    - self._check_clusters: Analyzes module-level AST children for shared name references to detect
      responsibility clusters (BLQ1202).

Cohesion:
    All logic revolves around one concern: determining whether a single Python file is too large or too
    multi-concern. The two private helpers (`_count_logical_lines`, `_check_clusters`) are both called from
    `visit_module` and operate on the same module-level AST node and its source file. They share the
    `_MAX_LOC` and `_MIN_CLUSTERS_TO_REPORT` module-level constants.

Separation:
    - quality_gates.py: QualityGatesChecker enforces code patterns (return None, bare except, test classes);
      this module enforces quantitative file metrics (LOC, clusters). They are orthogonal concerns.
    - layer_rules.py: LayerRulesChecker validates import architecture; this module validates file size.
    - init_rules.py: InitRulesChecker validates __init__.py content; this module applies to all Python files.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `FileSizeRulesChecker` into Pylint during plugin startup.
    - Pylint's module visitor: Calls `visit_module(node)` on every Python module in the linted source tree.

State and side effects:
    None, keeps no persistent state. The checker reads source files via `Path.read_text()` during
    `visit_module` but does not cache or store results. The `_check_clusters` method builds ephemeral
    `defaultdict` and `frozenset` structures from AST nodes that are discarded after the visit.

Invariants:
    - `_MAX_LOC` (1200) is the hard limit for logical lines; exceeding it always triggers BLQ1201.
    - `_MIN_CLUSTERS_TO_REPORT` (3) is the minimum number of clusters before BLQ1202 fires.
    - Files under `pytest_bdd_testing/` are always exempt from both checks.
    - Cluster detection requires at least 2 members sharing a key to count as a cluster.
    - Unreadable files (OSError, UnicodeDecodeError) are silently skipped.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

# init: allow
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

_MAX_LOC = 1200
_MIN_CLUSTERS_TO_REPORT = 3


class FileSizeRulesChecker(BaseChecker):
    """
    Acts as a Pylint `BaseChecker` that visits every Python module in the linted project and validates
    two quantitative f.

    Responsibility:
        Acts as a Pylint `BaseChecker` that visits every Python module in the linted project and validates
        two quantitative file-size constraints: BLQ1201 flags files exceeding 1200 logical lines of code
        (non-blank, non-comment lines), and BLQ1202 flags files containing 3 or more distinct responsibility
        clusters — groups of top-level classes/functions that share references to the same set of module-level
        names, suggesting the file should be split. Both checks skip files under `pytest_bdd_testing/` and
        silently skip unreadable files.

    Reason for existence:
        This checker is the single point of enforcement for file size policy in the pytest-bdd-ng project.
        Rather than relying on external tools or manual review, it programmatically detects oversized and
        over-concerned files during the normal Pylint linting pass. The responsibility-cluster detection is
        a custom heuristic not available in any off-the-shelf linter: it groups module-level definitions by
        the set of shared `nodes.Name` references they contain, then reports clusters with 2+ members.
        This class exists separately from other checkers because file-size rules are quantitative metrics
        with their own thresholds (`_MAX_LOC`, `_MIN_CLUSTERS_TO_REPORT`) and their own AST traversal
        strategy distinct from pattern-based or structural rules.

    Delegates:
        - self._count_logical_lines: Counts non-blank, non-comment lines in a source string.
        - self._check_clusters: Builds and reports responsibility clusters from module-level AST children.
        - Path.read_text: Reads the source file from disk for line counting.

    Cohesion:
        Every method in this class serves the single purpose of file-size validation. `visit_module` is the
        entry point, `_count_logical_lines` implements the LOC heuristic, and `_check_clusters` implements
        the cluster detection algorithm. All three operate on the same `nodes.Module` AST node and share the
        same exemption logic (skip `pytest_bdd_testing/`). No method has any purpose outside file-size checking.

    Separation:
        - QualityGatesChecker: Validates code patterns (return None, bare except, test classes) at the
          statement/expression level; this checker validates quantitative file-level metrics at the module level.
        - InitRulesChecker: Validates __init__.py file content rules; this checker applies to all Python files.
        - LayerRulesChecker: Validates import architecture; this checker validates file size.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker with Pylint.
        - Pylint module visitor: Calls `visit_module(node)` for every module in the linted tree.

    State and side effects:
        None, keeps no persistent state. The checker reads source files during `visit_module` but stores
        nothing between visits. The `_check_clusters` method creates temporary `defaultdict` and `frozenset`
        objects that are garbage-collected after the method returns.

    Invariants:
        - `_MAX_LOC` = 1200 is the universal threshold; any file exceeding it triggers BLQ1201.
        - `_MIN_CLUSTERS_TO_REPORT` = 3 is the minimum before BLQ1202 fires.
        - Files under `pytest_bdd_testing/` in their path are always exempt.
        - Cluster keys are `frozenset` of module-level names shared by 2+ definitions.
        - Cluster labels use uppercase letters A-Z (via `chr(64 + i)`); more than 26 clusters would produce
          non-letter labels.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
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
        Provide the Pylint visitor entry point for file-size validation.

        Responsibility:
            The Pylint visitor entry point for file-size validation. Reads the module's source file from disk,
            skips files under `pytest_bdd_testing/`, then delegates to `_count_logical_lines` for BLQ1201
            (line count check against `_MAX_LOC` of 1200) and to `_check_clusters` for BLQ1202
            (responsibility cluster detection). Silently returns if the file path is unavailable or the file
            cannot be read due to OSError or UnicodeDecodeError.

        Reason for existence:
            This method is the bridge between Pylint's AST-walking infrastructure and the file-size validation
            logic. Pylint calls `visit_module` once per module; this method translates that into the two
            specific checks the project requires. It handles all preconditions (file availability, exemption
            filtering, encoding safety) before delegating to the pure-logic helpers, ensuring those helpers
            never need to deal with missing files or encoding errors.

        Delegates:
            - self._count_logical_lines: Receives the raw source text and returns the logical line count for
              comparison against `_MAX_LOC`.
            - self._check_clusters: Receives the AST module node and its Path for cluster analysis and
              message reporting.

        Cohesion:
            This method orchestrates the two file-size checks; it does not contain the counting or cluster
            logic itself. Its sole responsibility is to gate conditions (file exists, not exempt, readable)
            and then dispatch to the appropriate helper. Both dispatched checks are file-size concerns.

        Separation:
            - visit_module in other checkers: Other checkers' visit_module methods handle entirely different
              concerns (import validation, noqa scanning, init rules); this one handles only file metrics.

        Main consumers:
            - Pylint's internal module visitor: Called automatically during the linting traversal.

        State and side effects:
            Reads the module's source file from disk via `Path.read_text()`. Calls `self.add_message()` to
            emit linting diagnostics. Does not cache or retain any state between calls.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=4
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Count the number of logical (non-blank, non-comment) lines in a Python source string.

        Responsibility:
            Counts the number of logical (non-blank, non-comment) lines in a Python source string. Iterates
            over each line, strips whitespace, and increments a counter for lines that are non-empty and do
            not start with `#`. This count is compared against `_MAX_LOC` (1200) to trigger BLQ1201.

        Reason for existence:
            This method exists as a standalone helper because the line-counting algorithm has a specific
            definition of "logical line" that differs from raw line count (excludes blanks and comments) and
            from astroid's own line metrics. It is pure logic with no AST dependency, taking only a string,
            making it trivially testable in isolation. Separating it from `visit_module` keeps the visitor
            method focused on orchestration.

        Delegates:
            - (none): This is a leaf method with no further delegation; it performs the counting inline.

        Cohesion:
            The method does one thing: increment a counter for each non-blank, non-comment line. There are
            no side branches or additional validation concerns.

        Separation:
            - _check_clusters: Deals with AST-based cluster analysis; this method deals with raw text counting.
              They are complementary but independent file-size metrics.

        Main consumers:
            - FileSizeRulesChecker.visit_module: The sole caller, which compares the return value against
              `_MAX_LOC`.

        State and side effects:
            None, pure function. Takes a string and returns an integer. No I/O, no mutation of `self` or
            external state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        count = 0
        for raw_line in source.splitlines():
            stripped = raw_line.strip()
            if stripped and not stripped.startswith("#"):
                count += 1
        return count

    def _check_clusters(self, node: nodes.Module, path: Path) -> None:
        """
        Detect responsibility clusters within a module by analyzing top-level class and function
        definitions.

        Responsibility:
            Detects responsibility clusters within a module by analyzing top-level class and function
            definitions. For each top-level definition, collects all `nodes.Name` references within its body
            and intersects them with the set of module-level names. Definitions sharing the same set of
            referenced module-level names form a cluster. If 3 or more clusters with 2+ members each are
            found, emits BLQ1202 with a suggestion string labeling clusters A, B, C, etc. with their member
            names.

        Reason for existence:
            This method implements a custom heuristic for detecting files that should be split: if multiple
            top-level classes/functions all reference the same set of module-level symbols, they likely form
            a cohesive sub-concern that could be extracted. No existing Pylint checker provides this analysis.
            The algorithm is kept as a private method rather than a standalone function because it depends on
            the checker's `self.add_message()` for reporting and on `nodes_of_class(nodes.Name)` for AST
            traversal.

        Delegates:
            - child.nodes_of_class(nodes.Name): Traverses each definition's AST subtree to collect all Name
              node references.
            - self.add_message: Emits the BLQ1202 diagnostic with cluster count and suggestion string.

        Cohesion:
            Every line of this method serves the cluster detection algorithm: collecting module-level names,
            iterating children, building frozenset keys, filtering reportable clusters, formatting suggestions.
            There are no unrelated operations.

        Separation:
            - _count_logical_lines: Handles the simpler BLQ1201 line count; this method handles the more
              complex BLQ1202 cluster analysis. They are orthogonal file-size checks.

        Main consumers:
            - FileSizeRulesChecker.visit_module: The sole caller, invoked after the line-count check passes.

        State and side effects:
            Builds temporary in-memory data structures (`set` of module-level names, `defaultdict` of
            clusters) that are discarded after the method returns. Calls `self.add_message()` when clusters
            are detected, which may produce linting output. No file I/O beyond what `visit_module` already
            performed.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
