"""
Enforces three code-quality rules that apply to non-test, non-exempt source files in the
pytest-bdd-ng project.

Responsibility:
    Enforces three code-quality rules that apply to non-test, non-exempt source files in the
    pytest-bdd-ng project. BLQ901 (no-return-none) forbids bare `return None` in non-hook
    functions — callers should use `Nothing` (Maybe) or `Failure(reason)` (Result) instead.
    BLQ902 (bare-except-exception) forbids bare `except Exception:` blocks without logging —
    requiring either `logger.warning(exc_info=True)` or `logger.exception()` inside the handler
    body, or a `# noqa: BLE001` / `# noqa: BLQ902` comment. BLQ903 (no-test-class) forbids
    class-based tests in test files — the project uses pytest-style functions exclusively. The
    checker maintains a per-file line cache (`_lines_cache`) to avoid re-reading files for the
    noqa-suppression check in `_has_noqa_for_rule`.

Reason for existence:
    This module encodes three project-specific quality standards that go beyond what off-the-shelf
    linters provide. The `return None` prohibition is unique to this project's use of Maybe/Result
    monadic types: returning `None` is an anti-pattern that should be replaced with explicit
    `Nothing()` or `Failure(reason)`. The bare-except rule is stricter than standard linters: it
    requires not just avoiding bare `except:`, but also requiring logging for `except Exception:`.
    The test-class prohibition enforces the project's pytest-style-only testing convention. These
    three rules are co-located because they share the same line-caching infrastructure
    (`_get_lines`, `_line_at`, `_has_noqa_for_rule`) for noqa suppression detection, and they
    all operate at the statement/expression level of the AST rather than the module or import level.

Delegates:
    - self._get_lines: Caches and returns source file lines for a given AST node's file.
    - self._line_at: Safely retrieves a single line from the cached lines list by 1-based number.
    - self._has_noqa_for_rule: Checks if a noqa comment on the current or previous line suppresses
      a specific rule, enabling legitimate exceptions.
    - self._has_exception_logging: Searches an exception handler's body for supported logging calls.
    - self._is_supported_logging_call: Determines if a `Call` node is `logger.warning(exc_info=True)`
      or `logger.exception()`.
    - self.add_message: Reports BLQ901, BLQ902, or BLQ903 violations.

Cohesion:
    All logic in this module serves code-quality enforcement. The three rules (return None, bare
    except, test classes) share the common line-caching and noqa-checking infrastructure. The
    logging detection helpers (`_has_exception_logging`, `_is_supported_logging_call`) are specific
    to BLQ902 but are cleanly separated. The visitor methods (`visit_return`, `visit_excepthandler`,
    `visit_classdef`) each handle one rule, keeping the rule logic independent despite sharing
    infrastructure.

Separation:
    - file_size_rules.py: FileSizeRulesChecker handles quantitative file metrics; this module
      handles qualitative code patterns.
    - init_rules.py: InitRulesChecker handles __init__.py structural rules; this module handles
      general code patterns applicable to all files.
    - plugin_patterns.py: PluginPatternsChecker handles plugin-specific conventions; this module
      handles general code quality that applies project-wide (with directory exemptions).

Main consumers:
    - pytest_bdd._pylint.register(): Loads `QualityGatesChecker` into Pylint during plugin startup.
    - Pylint visitors: Calls `visit_return`, `visit_excepthandler`, and `visit_classdef` during
      AST traversal.

State and side effects:
    Maintains a `_lines_cache: dict[str, list[str]]` mapping file paths to their source lines
    for noqa-suppression lookups. The cache is populated lazily on first access to each file and
    persists for the Pylint session lifetime. This avoids re-reading files that are visited
    multiple times (once per module, once per contained node). Visitor methods call
    `self.add_message()` to emit diagnostics.

Invariants:
    - BLQ901: Exempt directories are `{"pytest_bdd_testing", "_pylint", "plugin", "util", "script",
      "scenario_locator"}` — files under these paths never trigger BLQ901.
    - BLQ901: Functions with names starting with `pytest_` or `_pytest_` (pytest hooks) are exempt.
    - BLQ901: Only `return None` (Const node with value None) triggers; `return` with no value
      (implicit None) is NOT caught.
    - BLQ902: Only `except Exception:` (Name node matching "Exception") triggers; `except ValueError:`
      or bare `except:` do not.
    - BLQ902: Logging is detected via `logger.warning(exc_info=True)` or `logger.exception()` calls
      inside the handler body; any form of these calls satisfies the requirement.
    - BLQ902: `# noqa: BLE001` or `# noqa: BLQ902` on the current or previous line suppresses the check.
    - BLQ903: Only fires for classes with `test_`-prefixed methods in test files (under
      `pytest_bdd_testing` or files named `test_*.py`).
    - Line cache entries for unreadable files are stored as empty lists.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=4
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

# init: allow
# pylint: disable=file-too-long
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class QualityGatesChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that enforces three project-specific code quality gates on non-test
    source files.

    Responsibility:
        A Pylint `BaseChecker` that enforces three project-specific code quality gates on non-test
        source files. BLQ901 (`visit_return`) flags `return None` in non-hook functions — the project
        uses `Nothing` (Maybe) or `Failure(reason)` (Result) monadic types instead, so bare None
        returns are forbidden outside pytest hooks and exempt directories. BLQ902
        (`visit_excepthandler`) flags `except Exception:` blocks that lack logging — the handler must
        contain `logger.warning(exc_info=True)` or `logger.exception()`, unless suppressed by a
        `# noqa: BLE001` or `# noqa: BLQ902` comment. BLQ903 (`visit_classdef`) flags test classes
        (classes with `test_`-prefixed methods) in test files, enforcing the project's pytest-style
        function-only convention. Maintains a file-line cache for efficient noqa-suppression lookups.

    Reason for existence:
        This checker encodes quality standards that are unique to the pytest-bdd-ng project and not
        available in standard linters. The `return None` rule enforces the project's adoption of
        monadic error handling — returning `None` is an implicit failure that callers can't
        distinguish from a missing value, whereas `Nothing()` and `Failure(reason)` are explicit.
        The bare-except rule is stricter than standard `bare-except` checks: it targets `except
        Exception:` specifically (not bare `except:`) and requires logging as the minimum acceptable
        handling. The test-class rule enforces a testing style convention. These rules are co-located
        because they share the caching and noqa-checking infrastructure, and they all represent
        project-specific quality gates rather than general-purpose linting rules.

    Delegates:
        - self._get_lines: Lazily reads and caches source file lines for noqa lookups.
        - self._line_at: Retrieves a single line by 1-based index from the cache.
        - self._has_noqa_for_rule: Checks for suppressing noqa comments on or near a node.
        - self._has_exception_logging: Walks an except handler body for logging calls.
        - self._is_supported_logging_call: Validates a call node is a recognized logging pattern.
        - self.add_message: Emits BLQ901, BLQ902, or BLQ903 diagnostics.

    Cohesion:
        All methods support the three quality gate rules. The caching infrastructure (`_get_lines`,
        `_line_at`, `_has_noqa_for_rule`) is shared by BLQ901 and BLQ902. The logging detection
        helpers (`_has_exception_logging`, `_is_supported_logging_call`) are specific to BLQ902.
        The three visitor methods each implement one rule independently, but they share the common
        theme of "code quality enforcement for the pytest-bdd-ng project."

    Separation:
        - FileSizeRulesChecker: Handles quantitative file metrics (LOC, clusters); this checker
          handles qualitative code patterns.
        - InitRulesChecker: Handles __init__.py structural rules; this checker handles general
          code patterns across all files.
        - PluginPatternsChecker: Handles plugin-specific conventions (file structure, cross-plugin
          imports, stash access); this checker handles language-level code patterns.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint visitors: Dispatches `visit_return`, `visit_excepthandler`, and `visit_classdef`.

    State and side effects:
        Holds `_lines_cache: dict[str, list[str]]` — a file-path to source-lines mapping populated
        lazily by `_get_lines`. The cache persists for the Pylint session to avoid re-reading files.
        Unreadable files are cached as empty lists. Visitor methods call `self.add_message()`.
        No other persistent state or file I/O beyond cache population.

    Invariants:
        - BLQ901 exempt directories: `pytest_bdd_testing`, `_pylint`, `plugin`, `util`, `script`,
          `scenario_locator`.
        - BLQ901 exempt functions: names starting with `pytest_` or `_pytest_`.
        - BLQ901 only fires for explicit `return None` (Const node), not implicit `return`.
        - BLQ902 fires only for `except Exception:` (Name node, name="Exception").
        - BLQ902 satisfied by `logger.warning(exc_info=True)` or `logger.exception()` in handler body.
        - BLQ902 suppressible by `# noqa: BLE001` or `# noqa: BLQ902` on current or previous line.
        - BLQ903 fires only for classes with `test_` methods in test-pathed files.
        - Line cache entries are never evicted; memory grows with number of unique files visited.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=4
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    name = "quality-gates"

    msgs = {
        "R9001": (
            "BLQ901: return None in non-hook function - use Nothing (Maybe) or Failure(reason) (Result) instead",
            "no-return-none",
            "BLQ901: return None in non-hook function is forbidden.",
        ),
        "W9002": (
            "BLQ902: bare except Exception: without logging - add logger.warning(exc_info=True) or # noqa: BLE001",
            "bare-except-exception",
            "BLQ902: bare except Exception: without logging is forbidden.",
        ),
        "R9003": (
            "BLQ903: test class found — use pytest-style functions instead of class-based tests",
            "no-test-class",
            "BLQ903: test class found.",
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        """
        Initialize the checker by calling the parent `BaseChecker.__init__` and creating an
        empty `_lines_cache` dict.

        Responsibility:
            Initializes the checker by calling the parent `BaseChecker.__init__` and creating an
            empty `_lines_cache` dict. The cache maps file paths to their source lines (as
            `list[str]`) and is populated lazily by `_get_lines` on first access to each file.

        Reason for existence:
            The line cache is essential for noqa-suppression detection in `_has_noqa_for_rule`,
            which needs to inspect the source text of the current and previous lines. Without
            caching, every noqa check would re-read the file from disk, which is wasteful since
            the same file may be visited many times (once per module, once per contained node).

        Delegates:
            - super().__init__: Standard Pylint BaseChecker initialization.

        Cohesion:
            This method does exactly one initialization step: create the cache dict. Nothing else.

        Separation:
            - _get_lines: Populates the cache; this constructor only creates the empty container.

        Main consumers:
            - pytest_bdd._pylint.register(): Instantiates the checker during plugin registration.

        State and side effects:
            Sets `self._lines_cache = {}`. No I/O, no external mutations.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        super().__init__(linter)
        self._lines_cache: dict[str, list[str]] = {}

    def _get_lines(self, node: nodes.NodeNG) -> list[str]:
        """
        Lazily reads and caches a source file's lines.

        Responsibility:
            Lazily reads and caches a source file's lines. If the file path (from
            `node.root().file`) is not yet in `_lines_cache`, reads the file via `Path.read_text()`
            and splits into lines. If the file cannot be read (any `Exception`), stores an empty
            list to avoid repeated failed reads. Returns the cached line list for the file.

        Reason for existence:
            This method provides the caching layer for noqa-suppression detection. Multiple
            visitor methods may need to inspect source lines for the same file, and reading the
            file from disk on every check would be wasteful. The lazy-population pattern means
            files are only read when a noqa check is actually needed, not during every visit.

        Delegates:
            - Path.read_text: Reads the source file from disk for initial cache population.

        Cohesion:
            This method does one thing: return the line list for a file, reading it from disk
            if not already cached. The caching logic is self-contained.

        Separation:
            - _line_at: Consumes the cached lines; this method provides them.
            - _has_noqa_for_rule: Uses both `_get_lines` and `_line_at` for noqa detection.

        Main consumers:
            - QualityGatesChecker._has_noqa_for_rule: Called to get source lines for noqa checking.

        State and side effects:
            Mutates `self._lines_cache` by adding new entries (file path → list of lines or empty
            list). Reads files from disk via `Path.read_text()`. No other side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        filepath = node.root().file
        if not filepath:
            return []
        if filepath not in self._lines_cache:
            try:
                self._lines_cache[filepath] = Path(filepath).read_text(encoding="utf-8").splitlines()
            except Exception:  # noqa: BLE001  -- file read errors are non-fatal; missing lines treated as empty list
                self._lines_cache[filepath] = []
        return self._lines_cache[filepath]

    def _line_at(self, lines: list[str], line_number: int) -> str:
        """
        Safely retrieves a single source line from the given lines list using a 1-based
        line number.

        Responsibility:
            Safely retrieves a single source line from the given lines list using a 1-based
            line number. Returns an empty string if the line number is out of bounds (less than
            1 or greater than the list length). Performs index adjustment (line_number - 1) for
            0-based list access.

        Reason for existence:
            This method provides bounds-safe line access for noqa detection. AST node line
            numbers are 1-based, and `_has_noqa_for_rule` needs to check the current line
            and the previous line (line_number - 1). Without bounds checking, an out-of-range
            line number would raise IndexError. The method exists as a tiny helper to avoid
            repeating the bounds check at each call site.

        Delegates:
            - (none): Simple list indexing with bounds checking.

        Cohesion:
            This method does exactly one thing: safe line retrieval by 1-based number. Pure
            utility with no knowledge of the caller's purpose.

        Separation:
            - _get_lines: Provides the lines list; this method indexes into it.

        Main consumers:
            - QualityGatesChecker._has_noqa_for_rule: Called twice (current line and previous
              line) for noqa detection.

        State and side effects:
            None, pure function. No I/O, no mutations.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if line_number < 1 or line_number > len(lines):
            return ""
        return lines[line_number - 1]

    def _has_noqa_for_rule(self, node: nodes.NodeNG, rules: tuple[str, ...]) -> bool:
        """
        Check whether a noqa comment on the current line or the previous line suppresses
        any of the given rules.

        Responsibility:
            Checks whether a noqa comment on the current line or the previous line suppresses
            any of the given rules. Fetches source lines via `_get_lines` and `_line_at`, then
            checks two conditions: (1) if the line contains "noqa" without a colon (bare noqa,
            suppresses everything), or (2) if the line contains "noqa:" followed by any of the
            specified rule codes. Returns `True` if suppression is detected, `False` otherwise.

        Reason for existence:
            This method provides the escape hatch for quality gate rules — developers can
            legitimately suppress BLQ901 or BLQ902 with a documented noqa comment. It checks
            both the current line and the previous line because `except Exception:` and the
            noqa comment may be on different lines. The two-condition check (bare noqa vs
            specific rule codes) mirrors the noqa convention: bare noqa suppresses all rules,
            while `# noqa: BLQ901` suppresses only that rule.

        Delegates:
            - self._get_lines: Fetches cached source lines for the file.
            - self._line_at: Retrieves specific lines by number from the cache.

        Cohesion:
            This method does one thing: check for rule-suppressing noqa comments. The logic is
            self-contained — it doesn't know which rule is being checked, only the rule codes.

        Separation:
            - visit_return / visit_excepthandler: Both call this method with their respective
              rule codes; the method is rule-agnostic.
            - NoqaRulesChecker: Validates noqa comment format; this method consumes them for
              suppression detection without validating format.

        Main consumers:
            - QualityGatesChecker.visit_return: Checks for BLQ901 / no-return-none suppression.
            - QualityGatesChecker.visit_excepthandler: Checks for BLE001 / BLQ902 suppression.

        State and side effects:
            May trigger `_get_lines` which reads a file from disk and populates the cache.
            No other state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        lines = self._get_lines(node)
        current_line = self._line_at(lines, node.lineno)
        previous_line = self._line_at(lines, node.lineno - 1)
        for line in (current_line, previous_line):
            if "noqa" in line:
                if "noqa:" not in line:
                    return True
                if any(rule in line for rule in rules):
                    return True
        return False

    def visit_return(self, node: nodes.Return) -> None:
        """
        Enforces BLQ901: flags `return None` statements in non-hook, non-exempt functions.

        Responsibility:
            Enforces BLQ901: flags `return None` statements in non-hook, non-exempt functions.
            Checks if the file path contains any exempt directory (`pytest_bdd_testing`, `_pylint`,
            `plugin`, `util`, `script`, `scenario_locator`). Verifies that the return value is
            a `Const` node with value `None` (not implicit `return`). Ensures the enclosing scope
            is a function (not a module or class body). Exempts pytest hooks (names starting with
            `pytest_` or `_pytest_`). Checks for suppressing noqa comments before emitting BLQ901.

        Reason for existence:
            This method enforces the project's monadic error handling convention. The pytest-bdd-ng
            codebase uses `Nothing` (Maybe type) and `Failure(reason)` (Result type) for explicit
            absence/error signaling. A bare `return None` is ambiguous — it could mean "no result"
            or "an error occurred." The directory exemptions prevent this rule from firing on test
            code, the pylint plugin itself, and utility code where `return None` may be appropriate.
            The hook exemption exists because pytest hooks conventionally return None.

        Delegates:
            - self._has_noqa_for_rule: Checks for BLQ901 / no-return-none suppression comments.
            - self.add_message: Emits BLQ901 when a violation is found.

        Cohesion:
            This method implements exactly one rule (BLQ901) with all its conditions and exemptions.
            It does not handle BLQ902 or BLQ903.

        Separation:
            - visit_excepthandler: Handles BLQ902 (bare except); unrelated to return statements.
            - visit_classdef: Handles BLQ903 (test classes); unrelated to return statements.

        Main consumers:
            - Pylint's return visitor: Called automatically for every `Return` node.

        State and side effects:
            May call `_has_noqa_for_rule` which accesses the line cache. Calls `self.add_message()`
            for violations. No persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        filepath = node.root().file
        if not filepath:
            return
        # Exempt non-core directories and testing
        exempt_dirs = {"pytest_bdd_testing", "_pylint", "plugin", "util", "script", "scenario_locator"}
        if any(d in filepath for d in exempt_dirs):
            return

        # Check if value is None
        if not (isinstance(node.value, nodes.Const) and node.value.value is None):
            return

        # Check if we are inside a function scope
        scope = node.scope()
        if not isinstance(scope, (nodes.FunctionDef, nodes.AsyncFunctionDef)):
            return

        # Exempt pytest hooks
        if scope.name.startswith(("pytest_", "_pytest_")):
            return

        # Check for noqa comments
        if self._has_noqa_for_rule(node, ("BLQ901", "no-return-none")):
            return

        self.add_message("no-return-none", node=node)

    def visit_excepthandler(self, node: nodes.ExceptHandler) -> None:
        """
        Enforces BLQ902: flags `except Exception:` blocks that lack proper logging.

        Responsibility:
            Enforces BLQ902: flags `except Exception:` blocks that lack proper logging. Checks that
            the handler's type is a `Name` node with name `"Exception"` (not bare `except:`, not
            `except ValueError:`). Skips files under `pytest_bdd_testing`. Checks for suppressing
            noqa comments (`BLE001` or `BLQ902`). If the handler body contains a supported logging
            call (verified by `_has_exception_logging`), the check passes. Otherwise, emits BLQ902.

        Reason for existence:
            This method enforces the rule that catching `Exception` without logging is a code smell.
            Silently swallowing exceptions hides bugs and makes debugging difficult. The rule
            requires at minimum `logger.warning(exc_info=True)` or `logger.exception()` — either
            provides visibility into the suppressed error. The check targets `except Exception:`
            specifically because catching the base Exception class is the broadest possible catch
            and most likely to hide unexpected errors.

        Delegates:
            - self._has_noqa_for_rule: Checks for BLE001 / BLQ902 suppression comments.
            - self._has_exception_logging: Walks the handler body for supported logging calls.
            - self.add_message: Emits BLQ902 when a violation is found.

        Cohesion:
            This method implements exactly one rule (BLQ902). The exception type check, file
            exemption, noqa suppression, and logging detection are all steps in the single
            "bare except without logging" check.

        Separation:
            - visit_return: Handles BLQ901 (return None); unrelated to exception handling.
            - visit_classdef: Handles BLQ903 (test classes); unrelated to exception handling.
            - _has_exception_logging / _is_supported_logging_call: These helpers perform the
              detailed logging detection; this method orchestrates the full check.

        Main consumers:
            - Pylint's exception handler visitor: Called for every `ExceptHandler` node.

        State and side effects:
            May call `_has_noqa_for_rule` which accesses the line cache. Calls
            `_has_exception_logging` which traverses the handler body AST. Calls
            `self.add_message()` for violations. No persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        filepath = node.root().file
        if filepath and "pytest_bdd_testing" in filepath:
            return

        # Check if handler handles Exception specifically
        if not (isinstance(node.type, nodes.Name) and node.type.name == "Exception"):
            return

        # Check for noqa comments
        if self._has_noqa_for_rule(node, ("BLE001", "BLQ902")):
            return

        # Check for logging inside handler body
        if self._has_exception_logging(node):
            return

        self.add_message("bare-except-exception", node=node)

    def _has_exception_logging(self, handler: nodes.ExceptHandler) -> bool:
        """
        Walk the body of an exception handler looking for supported logging calls.

        Responsibility:
            Walks the body of an exception handler looking for supported logging calls. Iterates
            over each statement in `handler.body`, then recursively searches for `Call` nodes via
            `nodes_of_class(nodes.Call)`. For each call found, delegates to
            `_is_supported_logging_call` to determine if it matches the required logging patterns
            (`logger.warning(exc_info=True)` or `logger.exception()`). Returns `True` as soon as
            a supported call is found; returns `False` if no supported call exists.

        Reason for existence:
            This method performs the AST traversal needed to find logging calls within an exception
            handler. The recursive search via `nodes_of_class` is necessary because the logging call
            may be nested inside other statements (e.g., inside an `if` block or a `with` statement).
            The method is separate from `visit_excepthandler` to keep the visitor method focused on
            orchestration and the logging detection self-contained and testable.

        Delegates:
            - stmt.nodes_of_class(nodes.Call): Recursively finds all Call nodes in a statement subtree.
            - self._is_supported_logging_call: Validates whether a Call node matches the required
              logging patterns.

        Cohesion:
            This method does exactly one thing: search handler body for supported logging calls.
            The iteration and delegation are straightforward.

        Separation:
            - _is_supported_logging_call: Validates individual call nodes; this method finds them.
            - visit_excepthandler: Calls this method as part of the BLQ902 check.

        Main consumers:
            - QualityGatesChecker.visit_excepthandler: The sole caller.

        State and side effects:
            None, pure AST traversal. No I/O, no state changes. The `nodes_of_class` call may
            traverse large subtrees but does not modify them.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        for stmt in handler.body:
            for child in stmt.nodes_of_class(nodes.Call):
                if self._is_supported_logging_call(child):
                    return True
        return False

    def _is_supported_logging_call(self, call: nodes.Call) -> bool:
        """
        Validate whether an AST `Call` node represents a supported logging pattern for the
        BLQ902 rule.

        Responsibility:
            Validates whether an AST `Call` node represents a supported logging pattern for the
            BLQ902 rule. Checks that the call is an attribute access (e.g., `logger.warning(...)`)
            on an object named `logger` or `logging`. Two patterns are accepted:
            (1) `logger.exception()` — any call to `.exception()` on a logger object passes;
            (2) `logger.warning(exc_info=True)` — a call to `.warning()` passes only if it has
            a keyword argument `exc_info` with the literal value `True`. All other call patterns
            return `False`.

        Reason for existence:
            This method encapsulates the specific logging API knowledge needed for BLQ902. The
            project uses Python's standard `logging` module, and the two accepted patterns
            (`logger.exception()` and `logger.warning(exc_info=True)`) both provide stack trace
            information via `exc_info`. The `.exception()` method inherently includes exception
            info, while `.warning()` requires the explicit `exc_info=True` keyword. This method
            is separate from `_has_exception_logging` to keep the logging pattern logic isolated
            and testable.

        Delegates:
            - (none): Performs AST node type checks and attribute comparisons inline.

        Cohesion:
            This method does one thing: decide if a call node is a recognized logging pattern.
            The two branches (exception vs warning with exc_info) cover the two accepted forms.

        Separation:
            - _has_exception_logging: Finds call nodes; this method validates them.
            - visit_excepthandler: The rule orchestrator; doesn't know about logging API details.

        Main consumers:
            - QualityGatesChecker._has_exception_logging: Called for each Call node found in
              the handler body.

        State and side effects:
            None, pure function over AST nodes. No I/O, no mutations.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if not isinstance(call.func, nodes.Attribute):
            return False
        if not (isinstance(call.func.expr, nodes.Name) and call.func.expr.name in {"logger", "logging"}):
            return False

        if call.func.attrname == "exception":
            return True
        if call.func.attrname != "warning":
            return False

        # For warning, look for exc_info=True
        if not call.keywords:
            return False
        for kw in call.keywords:
            if kw.arg == "exc_info" and isinstance(kw.value, nodes.Const) and kw.value.value is True:
                return True
        return False

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """
        Enforces BLQ903: flags test classes (classes containing methods with names starting
        with `test_`) in test files.

        Responsibility:
            Enforces BLQ903: flags test classes (classes containing methods with names starting
            with `test_`) in test files. Only fires for files under `pytest_bdd_testing/` or files
            whose name starts with `test_`. If the class has at least one method (FunctionDef or
            AsyncFunctionDef) whose name starts with `test_`, emits BLQ903. This enforces the
            project's convention of using pytest-style test functions exclusively, without
            class-based test organization.

        Reason for existence:
            This method enforces the project's testing style convention. pytest-bdd-ng uses
            function-based tests with fixtures for setup, avoiding the unittest-style class
            hierarchy. Class-based tests in this codebase are an anti-pattern that suggests
            unfamiliarity with the project's conventions. The check is scoped to test directories
            and test files to avoid flagging legitimate non-test classes in source code.

        Delegates:
            - self.add_message: Emits BLQ903 when a test class is found.

        Cohesion:
            This method implements exactly one rule (BLQ903). The file-path check, method-name
            check, and message emission are all steps in the single "no test classes" check.

        Separation:
            - visit_return: Handles BLQ901 (return None); unrelated to class definitions.
            - visit_excepthandler: Handles BLQ902 (bare except); unrelated to class definitions.

        Main consumers:
            - Pylint's class definition visitor: Called automatically for every `ClassDef` node.

        State and side effects:
            Calls `self.add_message()` for violations. No I/O, no state changes.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        filepath = node.root().file
        if not filepath:
            return

        # Check if we are inside a test/cases directory or test file
        if not ("pytest_bdd_testing" in filepath or Path(filepath).name.startswith("test_")):
            return

        # Check if the class has any test methods
        has_test_methods = False
        for item in node.body:
            if isinstance(item, (nodes.FunctionDef, nodes.AsyncFunctionDef)) and item.name.startswith("test_"):
                has_test_methods = True
                break

        if has_test_methods:
            self.add_message("no-test-class", node=node)
