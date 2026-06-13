"""
Enforces project conventions for `# type: ignore` comments by scanning every Python
source file line-by-line during `.

Responsibility:
    Enforces project conventions for `# type: ignore` comments by scanning every Python
    source file line-by-line during `visit_module`. Two rules are validated: BLQ1101
    (bare-type-ignore) fires when a line contains a bare `# type: ignore` without an
    error code in brackets, requiring the format `# type: ignore[error-code]  # reason`;
    BLQ1102 (missing-type-ignore-explanation) fires when a `# type: ignore[error-code]`
    comment specifies an error code but lacks a trailing explanation comment after the
    closing bracket. Both rules use compiled regex patterns (`_BARE_IGNORE_RE` and
    `_NO_EXPLANATION_RE`) applied to each stripped source line. Files under hidden
    directories and standard tool directories are skipped.

Reason for existence:
    This module exists because bare `# type: ignore` comments are a type-safety hazard:
    they suppress ALL mypy type errors on a line without documenting which specific error
    is being suppressed or why. The two-tier check (bare then missing explanation) enforces
    the discipline of specifying WHAT error is ignored and WHY. The regex-based approach
    is used because `# type: ignore` comments are inline text annotations with no
    corresponding AST node. This module is separate from `noqa_rules.py` because
    `# type: ignore` and `# noqa` are different Python comment conventions with different
    required formats (`# type: ignore[code]  # reason` vs `# noqa: CODE  # reason`) and
    are enforced by different tools (mypy vs ruff/pylint). The file-skipping logic
    mirrors `noqa_rules.py` to maintain consistency in which files are checked.

Delegates:
    - Path.read_text: Reads source files from disk for line-by-line scanning.
    - path.relative_to(Path.cwd()): Determines if a file is under a hidden directory.
    - re.compile / regex.search: Matches bare and unexplained type:ignore patterns
      against source lines.
    - self.add_message: Emits BLQ1101 or BLQ1102 diagnostics with line numbers and
      (for BLQ1102) the specific error code being ignored.

Cohesion:
    The entire module is focused on one concern: `# type: ignore` comment validation.
    The two regex constants are defined at module level and used exclusively by the single
    `visit_module` method. The file-skipping logic (hidden directories, `__pycache__`,
    `.git`, `.tox`, etc.) is shared with the broader type:ignore concern. There are no
    other methods, classes, or unrelated utilities in this module.

Separation:
    - noqa_rules.py: NoqaRulesChecker validates `# noqa` comments with a similar
      line-by-line scanning approach but enforces a different format and different
      message codes. The two are separate because noqa and type:ignore are distinct
      Python comment conventions for different tools.
    - quality_gates.py: QualityGatesChecker uses noqa comments for rule suppression
      detection but does not enforce type:ignore comment format.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `TypingRulesChecker` into Pylint during plugin
      startup.
    - Pylint's module visitor: Calls `visit_module(node)` for every module in the linted
      tree.
    - CI/CD: Ensures all type:ignore comments in the codebase are properly documented.

State and side effects:
    None, keeps no persistent state. `visit_module` reads source files from disk via
    `Path.read_text()` on each call, performs regex matching, and emits diagnostics via
    `self.add_message()`. No caching of file contents between visits.

Invariants:
    - `_BARE_IGNORE_RE` matches lines ending with `# type: ignore` with optional
      trailing whitespace, but NOT lines with bracketed error codes.
    - `_NO_EXPLANATION_RE` matches lines with `# type: ignore[CODE]` followed by
      optional whitespace and end-of-line — an error code is present but no
      explanation comment follows.
    - Bare type:ignore check runs before missing-explanation check; `continue` prevents
      a line from triggering both BLQ1101 and BLQ1102.
    - BLQ1102 message includes the extracted error code twice (once for display, once
      as part of the suggestion text).
    - Files under hidden directories (dot-prefixed relative to CWD) are always skipped.
    - Files in `__pycache__` and standard tool directories (`.git`, `.tox`, `.venv`,
      `.idea`, `.mypy_cache`, `.ruff_cache`) are always skipped.
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

_BARE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore\s*$")
_NO_EXPLANATION_RE = re.compile(r"#\s*type:\s*ignore\[([^\]]+)\]\s*$")


class TypingRulesChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that scans every Python source file for `# type: ignore`
    comment violations.

    Responsibility:
        A Pylint `BaseChecker` that scans every Python source file for `# type: ignore`
        comment violations. During `visit_module`, reads the entire source file line-by-line
        and applies two compiled regex patterns: `_BARE_IGNORE_RE` detects bare
        `# type: ignore` with no bracketed error code (BLQ1101), and `_NO_EXPLANATION_RE`
        detects `# type: ignore[error-code]` where an error code is specified but no
        trailing explanation comment is provided (BLQ1102). The BLQ1102 message includes
        the extracted error code so developers know exactly which suppression needs
        explanation. Files under hidden directories and standard tool directories
        (`__pycache__`, `.git`, `.tox`, `.venv`, `.idea`, `.mypy_cache`, `.ruff_cache`)
        are skipped, as are unreadable files.

    Reason for existence:
        This checker enforces the project's type-safety discipline: every `# type: ignore`
        must specify which mypy error is being suppressed AND why. A bare `# type: ignore`
        suppresses all type errors on a line, potentially hiding real bugs. Even with an
        error code, the lack of explanation makes it impossible for future developers to
        know whether the suppression is still needed. The checker uses regex rather than
        AST because type:ignore comments are inline text that astroid does not expose.
        It is separate from `NoqaRulesChecker` because `# type: ignore` and `# noqa`
        are different Python conventions with different format requirements and are
        consumed by different tools (mypy vs ruff/pylint). The file-skipping logic
        mirrors `NoqaRulesChecker` for consistency.

    Delegates:
        - Path.read_text: Reads the source file from disk for line-by-line scanning.
        - path.relative_to(Path.cwd()): Determines if the file is under a hidden directory.
        - _BARE_IGNORE_RE.search: Matches lines with bare `# type: ignore` (no brackets).
        - _NO_EXPLANATION_RE.search: Matches lines with `# type: ignore[CODE]` but no
          explanation; captures the error code for the message.
        - self.add_message: Emits BLQ1101 or BLQ1102 with line numbers and error codes.

    Cohesion:
        The entire class is focused on one concern: `# type: ignore` comment format
        validation. The single `visit_module` method contains all the logic (file reading,
        directory skipping, regex matching, message emission). There are no helper methods
        or shared state beyond the module-level regex constants.

    Separation:
        - NoqaRulesChecker: Validates `# noqa` comments with similar line-by-line scanning
          but different regex patterns and message codes. Both enforce comment documentation
          discipline but for different comment types consumed by different tools.
        - QualityGatesChecker._has_noqa_for_rule: Consumes noqa comments for suppression
          detection; this checker ensures type:ignore comments are well-formed independently.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint's module visitor: Calls `visit_module(node)` for every source file.
        - CI/CD: Enforces type:ignore comment discipline across the codebase.

    State and side effects:
        None, keeps no persistent state. Each `visit_module` call reads the file from
        disk, scans its lines, emits messages, and discards all data. No caching between
        calls.

    Invariants:
        - Bare type:ignore (BLQ1101) is checked before missing-explanation (BLQ1102);
          `continue` prevents a line from triggering both.
        - `_BARE_IGNORE_RE` matches `# type: ignore` with optional whitespace and
          end-of-line, but NOT when brackets follow.
        - `_NO_EXPLANATION_RE` captures the error code inside brackets via group(1) for
          inclusion in the BLQ1102 message.
        - Hidden directory detection uses both relative-to-CWD path checking and explicit
          set membership for standard hidden dirs.
        - Unreadable files (OSError, UnicodeDecodeError) are silently skipped.
        - Each line is checked independently; violations on multiple lines produce
          multiple messages.

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

    name = "typing-rules"

    msgs = {
        "W9021": (
            "BLQ1101: bare '# type: ignore' without error code. "
            "Add error code in brackets: '# type: ignore[error-code]  # brief reason'",
            "bare-type-ignore",
            "BLQ1101: Bare type ignore comments are forbidden.",
        ),
        "W9022": (
            "BLQ1102: '# type: ignore[%s]' missing explanation. Add explanation: '# type: ignore[%s]  # brief reason'",
            "missing-type-ignore-explanation",
            "BLQ1102: Explanation comment is required for type ignores.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Read the module's source file line-by-line and checks each line against two
        `# type: ignore` violation patterns.

        Responsibility:
            Reads the module's source file line-by-line and checks each line against two
            `# type: ignore` violation patterns. For each line: if `_BARE_IGNORE_RE` matches,
            emits BLQ1101 (bare type:ignore without error code) and skips to the next line;
            otherwise, if `_NO_EXPLANATION_RE` matches, extracts the error code from
            group(1) and emits BLQ1102 (type:ignore with code but no explanation). Files
            under hidden directories are skipped using the same logic as NoqaRulesChecker:
            relative-to-CWD dot-prefix check, plus explicit set of standard hidden dirs
            (`.git`, `.tox`, `.venv`, `.idea`, `.mypy_cache`, `.ruff_cache`, `__pycache__`).
            Unreadable files are silently skipped.

        Reason for existence:
            This is the sole entry point for type:ignore validation. Pylint calls it once
            per module. The line-by-line regex approach is used because type:ignore comments
            are text-level annotations with no corresponding AST node. The two-pattern
            approach (bare first, then missing explanation) enforces progressive discipline:
            specify WHAT error you're ignoring, then explain WHY. The `continue` after
            bare-type-ignore prevents double-reporting. The error code extraction via
            regex group(1) enables the diagnostic message to include the specific code.

        Delegates:
            - Path.read_text: Reads the source file content for line-by-line scanning.
            - path.relative_to(Path.cwd()): Checks if the file is under a hidden directory.
            - _BARE_IGNORE_RE.search: Matches lines with bare `# type: ignore`.
            - _NO_EXPLANATION_RE.search: Matches lines with error codes but no explanation;
              captures the error code via group(1).
            - self.add_message: Emits BLQ1101 or BLQ1102 with the violation's line number
              and (for BLQ1102) the error code.

        Cohesion:
            This method does exactly one thing: scan source lines for type:ignore violations.
            The directory skipping, file reading, regex matching, and message emission all
            serve this single purpose.

        Separation:
            - NoqaRulesChecker.visit_module: Scans for `# noqa` violations with different
              regex patterns but identical structural approach. Both are line-scanning
              visitors but for different comment types.
            - QualityGatesChecker.visit_module: Handles unrelated quality gate checks;
              does not perform line-by-line comment scanning.

        Main consumers:
            - Pylint's module visitor: Called automatically for every module in the linted
              tree.

        State and side effects:
            Reads the source file from disk via `Path.read_text()`. Calls
            `self.add_message()` to emit diagnostics. Does not cache or retain any state
            between visits.

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

            if _BARE_IGNORE_RE.search(stripped):
                self.add_message("bare-type-ignore", line=line_no, node=node)
                continue

            match_no_expl = _NO_EXPLANATION_RE.search(stripped)
            if match_no_expl:
                error_code = match_no_expl.group(1)
                self.add_message(
                    "missing-type-ignore-explanation",
                    line=line_no,
                    node=node,
                    args=(error_code, error_code),
                )
        return
