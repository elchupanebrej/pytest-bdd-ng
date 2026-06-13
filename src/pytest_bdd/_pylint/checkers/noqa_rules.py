"""
Enforces project conventions for `# noqa` comments by scanning every Python source file line-by-line
during `visit_mo.

Responsibility:
    Enforces project conventions for `# noqa` comments by scanning every Python source file line-by-line
    during `visit_module`. Two rules are validated: BLQ1701 (bare-noqa) fires when a line contains a bare
    `# noqa` or `# noqa:` with no error codes specified, requiring the format `# noqa: CODE  # reason`;
    BLQ1702 (missing-noqa-explanation) fires when a `# noqa: CODE` comment lists error codes but lacks
    a trailing explanation comment after the codes. Both rules use compiled regex patterns (`_BARE_NOQA_RE`
    and `_NO_EXPLANATION_RE`) applied to each stripped source line. Files under hidden directories
    (dot-prefixed, `__pycache__`, `.git`, `.tox`, `.venv`, `.idea`, `.mypy_cache`, `.ruff_cache`)
    are skipped.

Reason for existence:
    This module exists because bare `# noqa` comments are a code quality anti-pattern: they suppress ALL
    linting warnings on a line without documenting which warning is being suppressed or why. Over time,
    this hides real issues. The two-tier check (bare → missing explanation) enforces a progressive
    discipline: first specify WHAT you're suppressing, then explain WHY. The regex-based approach
    (rather than AST analysis) is necessary because `# noqa` comments are inline comments that astroid
    does not expose as structured nodes. The module is separate from `typing_rules.py` because noqa
    and type:ignore are different comment conventions with different required formats, even though both
    use line-by-line regex scanning.

Delegates:
    - Path.read_text: Reads source files to scan for noqa comments.
    - path.relative_to(Path.cwd()): Determines if a file is under a hidden directory for skipping.
    - re.compile / regex.search: Matches bare and unexplained noqa patterns against source lines.
    - self.add_message: Emits BLQ1701 or BLQ1702 diagnostics with line numbers.

Cohesion:
    The entire module is focused on one concern: noqa comment validation. The two regex constants are
    defined at module level and used exclusively by the single `visit_module` method. The file-skipping
    logic (hidden directories, `__pycache__`) is shared with the broader noqa concern. There are no
    other methods, classes, or unrelated utilities in this module.

Separation:
    - typing_rules.py: TypingRulesChecker validates `# type: ignore` comments with a similar line-by-line
      scanning approach but enforces a different format (`# type: ignore[code]  # reason`). The two are
      separate because noqa and type:ignore are distinct Python comment conventions.
    - quality_gates.py: QualityGatesChecker uses noqa comments for rule suppression detection
      (`_has_noqa_for_rule`), but as a consumer of noqa comments, not an enforcer of their format.
      This module ensures the noqa comments QualityGatesChecker relies on are well-formed.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `NoqaRulesChecker` into Pylint during plugin startup.
    - Pylint's module visitor: Calls `visit_module(node)` for every module in the linted tree.
    - CI/CD: Ensures all noqa comments in the codebase are properly documented.

State and side effects:
    None, keeps no persistent state. `visit_module` reads source files from disk via `Path.read_text()`
    on each call, performs regex matching, and emits diagnostics via `self.add_message()`. No caching
    of file contents between visits.

Invariants:
    - `_BARE_NOQA_RE` matches lines ending with `# noqa` or `# noqa:` with optional trailing whitespace.
    - `_NO_EXPLANATION_RE` matches lines with `# noqa: CODE1, CODE2` (codes only, no explanation after).
    - Bare noqa check runs before missing-explanation check; a line can trigger at most one violation.
    - Files under hidden directories (dot-prefixed relative to CWD) are always skipped.
    - Files in `__pycache__` directories are always skipped.
    - Unreadable files (OSError, UnicodeDecodeError) are silently skipped.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

# init: allow
from __future__ import annotations

import re
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

_BARE_NOQA_RE = re.compile(r"#\s*noqa(?::\s*)?$")
_NO_EXPLANATION_RE = re.compile(r"#\s*noqa:\s*[A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*\s*$")


class NoqaRulesChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that scans every Python source file for `# noqa` comment violations.

    Responsibility:
        A Pylint `BaseChecker` that scans every Python source file for `# noqa` comment violations.
        During `visit_module`, reads the entire source file line-by-line and applies two compiled regex
        patterns: `_BARE_NOQA_RE` detects bare `# noqa` or `# noqa:` with no error codes (BLQ1701),
        and `_NO_EXPLANATION_RE` detects `# noqa: CODE` with error codes but no trailing explanation
        (BLQ1702). Files under hidden directories (dot-prefixed, `__pycache__`, `.git`, `.tox`,
        `.venv`, `.idea`, `.mypy_cache`, `.ruff_cache`) are skipped, as are unreadable files.

    Reason for existence:
        This checker exists because the project requires all lint suppressions to be documented and
        justified. A bare `# noqa` suppresses every warning on a line with zero documentation — a
        maintenance hazard. The two-tier enforcement (must have codes AND explanation) ensures that
        future developers can understand why a warning was suppressed and whether the suppression
        is still needed. The checker uses regex rather than AST because noqa comments are inline
        text annotations that astroid does not expose. It is separate from the `TypingRulesChecker`
        because noqa and type:ignore have different format requirements and are conceptually
        different suppression mechanisms.

    Delegates:
        - Path.read_text: Reads the source file from disk for line-by-line scanning.
        - path.relative_to(Path.cwd()): Determines if the file is under a hidden directory.
        - _BARE_NOQA_RE.search / _NO_EXPLANATION_RE.search: Match the two violation patterns.
        - self.add_message: Emits BLQ1701 or BLQ1702 with the violation line number.

    Cohesion:
        The entire class is focused on one concern: noqa comment format validation. The single
        `visit_module` method contains all the logic (file reading, directory skipping, regex
        matching, message emission). There are no helper methods or shared state beyond the
        module-level regex constants.

    Separation:
        - TypingRulesChecker: Validates `# type: ignore` comments with similar line-by-line scanning
          but different regex patterns and message codes. Noqa and type:ignore are distinct Python
          comment conventions.
        - QualityGatesChecker._has_noqa_for_rule: Consumes noqa comments to check if a rule is
          suppressed; this checker ensures those comments are well-formed in the first place.
        - ResponsibilityDocsChecker: Validates docstring content; unrelated to inline comments.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint's module visitor: Calls `visit_module(node)` for every source file.
        - CI/CD: Enforces noqa comment discipline across the entire codebase.

    State and side effects:
        None, keeps no persistent state. Each `visit_module` call reads the file from disk, scans
        its lines, emits messages, and discards all data. No caching between calls.

    Invariants:
        - Bare noqa (BLQ1701) is checked before missing-explanation (BLQ1702); `continue` prevents
          a line from triggering both.
        - Hidden directory detection uses both relative-to-CWD path checking and explicit set
          membership for standard hidden dirs (`.git`, `.tox`, etc.).
        - Unreadable files (OSError, UnicodeDecodeError) are silently skipped.
        - Each line is checked independently; violations on multiple lines produce multiple messages.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    name = "noqa-rules"

    msgs = {
        "W9081": (
            "BLQ1701: bare '# noqa' comment. Specify warning codes: '# noqa: CODE  # brief reason'",
            "bare-noqa",
            "BLQ1701: Bare noqa comments are forbidden.",
        ),
        "W9082": (
            "BLQ1702: noqa comment missing explanation. Add explanation: '# noqa: CODE  # brief reason'",
            "missing-noqa-explanation",
            "BLQ1702: Explanation/reason is required for noqa comments.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Read the module's source file line-by-line and checks each line against two noqa violation
        patterns.

        Responsibility:
            Reads the module's source file line-by-line and checks each line against two noqa violation
            patterns. For each line: if `_BARE_NOQA_RE` matches, emits BLQ1701 (bare noqa) and skips
            to the next line; otherwise, if `_NO_EXPLANATION_RE` matches, emits BLQ1702
            (missing explanation). Files under hidden directories (relative to CWD or explicit set
            of `.git`, `.tox`, `.venv`, `.idea`, `.mypy_cache`, `.ruff_cache`, `__pycache__`) are
            skipped, as are files with no path or unreadable files.

        Reason for existence:
            This is the sole entry point for noqa validation. Pylint calls it once per module. The
            line-by-line regex approach is used because noqa comments are text-level annotations
            with no corresponding AST node. The two-pattern approach (bare first, then missing
            explanation) enforces a progressive discipline: you must specify WHAT you're suppressing
            before explaining WHY. The `continue` after bare-noqa prevents double-reporting.

        Delegates:
            - Path.read_text: Reads the source file content for line-by-line scanning.
            - path.relative_to(Path.cwd()): Checks if the file is under a hidden directory.
            - _BARE_NOQA_RE.search: Matches lines with bare `# noqa` comments.
            - _NO_EXPLANATION_RE.search: Matches lines with noqa codes but no explanation.
            - self.add_message: Emits BLQ1701 or BLQ1702 with the violation's line number.

        Cohesion:
            This method does exactly one thing: scan source lines for noqa violations. The directory
            skipping, file reading, regex matching, and message emission all serve this single purpose.

        Separation:
            - TypingRulesChecker.visit_module: Scans for `# type: ignore` violations with different
              regex patterns but identical structural approach. Both are line-scanning visitors but
              for different comment types.
            - QualityGatesChecker.visit_module: Handles unrelated quality gate checks; does not
              perform line-by-line comment scanning.

        Main consumers:
            - Pylint's module visitor: Called automatically for every module in the linted tree.

        State and side effects:
            Reads the source file from disk via `Path.read_text()`. Calls `self.add_message()` to
            emit diagnostics. Does not cache or retain any state between visits.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        filepath = node.file
        if not filepath:
            return

        path = Path(filepath)
        # Skip hidden folders relative to working directory, or specific standard hidden dirs
        # to avoid skipping files when checked out under a dot-prefixed home folder (like .local)
        try:
            rel_path = path.relative_to(Path.cwd())
            if any(part.startswith(".") for part in rel_path.parts) or "__pycache__" in path.parts:
                return
        except ValueError:
            if (
                any(part in {".git", ".tox", ".venv", ".idea", ".mypy_cache", ".ruff_cache"} for part in path.parts)
                or "__pycache__" in path.parts
            ):
                return

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        for line_no, line_text in enumerate(source.splitlines(), start=1):
            stripped = line_text.rstrip()

            if _BARE_NOQA_RE.search(stripped):
                self.add_message("bare-noqa", line=line_no, node=node)
                continue

            if _NO_EXPLANATION_RE.search(stripped):
                self.add_message("missing-noqa-explanation", line=line_no, node=node)
                continue
