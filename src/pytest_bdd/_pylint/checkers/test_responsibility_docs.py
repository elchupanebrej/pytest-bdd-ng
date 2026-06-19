"""
Validate that test functions (named `test_*`) in test files have complete test
responsibility documentation in their.

Responsibility:
    Validates that test functions (named `test_*`) in test files have complete test
    responsibility documentation in their docstrings. Enforces four rules specific to test
    code: BLQ920 (missing-test-responsibility-doc) flags missing required sections from the
    12-section test documentation template (Test target, Test type, Test scenario, BDD
    reference, Fixtures, Mocks, Side effects, Reduction, Escalation, Atomicity, Autonomy,
    Test quality score); BLQ921 (short-test-responsibility-doc) flags Test scenario sections
    shorter than 30 characters; BLQ922 (missing-test-quality-score) flags missing
    `#test-eval:criterion=N` tags for the 4 test quality criteria (isolation, determinism,
    setup_complexity, assertions_clarity) with values 1-5; BLQ923
    (unfilled-test-responsibility-placeholder) flags `<...>` template placeholders with 3+
    characters inside angle brackets that haven't been replaced.

Reason for existence:
    This module enforces a test documentation discipline that is distinct from the architecture
    documentation discipline enforced by `ResponsibilityDocsChecker`. Test functions need
    different documentation: what they test (Test target), how they test it (Test type,
    Test scenario), what fixtures and mocks they use, and quality scores for test-specific
    criteria (isolation, determinism, etc.). The minimum length for test descriptions is
    shorter (30 chars vs 140) because test scenarios are typically more concise than
    architectural justifications. Module-level validation is intentionally disabled
    (`visit_module` returns immediately) because test module docstrings may serve a
    different purpose than test function docstrings. The checker only operates on
    `test_`-prefixed functions in files that are recognized as test files (under `cases/`
    or `/tests/` directories, or starting with `tests/`, with filenames starting with
    `test_` or ending with `_test.py`, excluding `conftest.py`, `__init__.py`, and
    `test_pylint_checkers.py`).

Delegates:
    - self._parse_sections: Parses a test docstring into a dict of named sections by
      recognizing the 12 test-specific heading strings.
    - PLACEHOLDER_RE.search: Detects unfilled `<...>` template placeholders (3+ chars
      inside brackets) in section content.
    - re.search: Validates `#test-eval:criterion=N` score tag patterns.
    - self.add_message: Reports BLQ920-BLQ923 violations.

Cohesion:
    All logic in this module serves the single purpose of test function docstring validation.
    The `visit_module` method is a deliberate no-op. The `visit_functiondef` method contains
    all the filtering logic (test function name check, test file detection, section
    validation, score validation). The `_parse_sections` helper is specific to test
    documentation headings. The constants (`TEST_SCORE_CRITERIA`, `REQUIRED_TEST_SECTIONS`,
    `PLACEHOLDER_RE`, `MIN_LONG_SECTION`) are all test-documentation-specific.

Separation:
    - responsibility_docs.py: ResponsibilityDocsChecker validates architecture documentation
      for source code entities with different required sections (Responsibility, Reason for
      existence, etc.) and different score criteria (#arch-eval tags). This checker validates
      test documentation for test functions only.
    - quality_gates.py: QualityGatesChecker enforces code patterns including a test-class
      rule; this checker enforces test documentation completeness — related to tests but
      a different concern (documentation vs code patterns).

Main consumers:
    - pytest_bdd._pylint.register(): Loads `TestResponsibilityDocsChecker` into Pylint during
      plugin startup.
    - Pylint visitors: Calls `visit_module` (no-op) and `visit_functiondef` during AST
      traversal.
    - CI/CD: Ensures all test functions have complete test documentation before merge.

State and side effects:
    None, keeps no persistent state. Each `visit_functiondef` call is stateless — docstrings
    are extracted from AST nodes, parsed, and validated without caching. Messages are emitted
    via `self.add_message()`. No file I/O beyond what astroid already performed during parsing.

Invariants:
    - Only functions named `test_*` in recognized test files are checked.
    - Test files are identified by: filename starts with `test_` or ends with `_test.py`,
      AND path contains `cases/` or `/tests/` or starts with `tests/`, AND filename is not
      `conftest.py`, `__init__.py`, or `test_pylint_checkers.py`.
    - 12 required sections must all be present in every test function docstring.
    - `MIN_LONG_SECTION` = 30; only "Test scenario" is checked for minimum length.
    - `TEST_SCORE_CRITERIA` = 4 criteria; score values must be 1-5.
    - `PLACEHOLDER_RE` matches `<...>` with 3+ characters inside brackets (stricter than
      architecture doc checker to avoid false positives on short bracketed text).
    - Module-level validation is intentionally disabled.
    - `visit_functiondef` returns early if the parent module is not a `nodes.Module`.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import re
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

TEST_SCORE_CRITERIA = [
    "isolation",
    "determinism",
    "setup_complexity",
    "assertions_clarity",
]

REQUIRED_TEST_SECTIONS = [
    "Test target",
    "Test type",
    "Test scenario",
    "BDD reference",
    "Fixtures",
    "Mocks",
    "Side effects",
    "Reduction",
    "Escalation",
    "Atomicity",
    "Autonomy",
    "Test quality score",
]

PLACEHOLDER_RE = re.compile(r"<[^>\n]{3,}>")
MIN_LONG_SECTION = 30  # Allow shorter descriptions for tests compared to architecture


class TestResponsibilityDocsChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that validates test function docstrings in test files against
    a 12-section test documentation .

    Responsibility:
        A Pylint `BaseChecker` that validates test function docstrings in test files against
        a 12-section test documentation template. Operates only on `test_`-prefixed functions
        in files recognized as test files (under `cases/` or `/tests/`, filenames starting
        with `test_` or ending with `_test.py`, excluding `conftest.py`, `__init__.py`, and
        `test_pylint_checkers.py`). For each qualifying function, validates four conditions:
        (1) all 12 required sections are present (BLQ920), (2) the Test scenario section
        meets the 30-character minimum (BLQ921), (3) all 4 test quality criteria have valid
        `#test-eval:criterion=N` tags with values 1-5 (BLQ922), and (4) no `<...>` template
        placeholders with 3+ characters remain in any section (BLQ923). Module-level
        validation is disabled (`visit_module` is a no-op).

    Reason for existence:
        This checker enforces a documentation discipline specific to test code. While
        `ResponsibilityDocsChecker` validates architecture documentation for source
        entities, test functions need a different template focused on testing concerns:
        what is being tested, how, with what fixtures and mocks, and quality scores for
        test-specific criteria like isolation and determinism. The checker is separate
        because the templates, scoring criteria, minimum lengths, and file-targeting
        logic are all different from the architecture documentation checker. The stricter
        placeholder regex (3+ chars vs any content) avoids false positives on short
        bracketed text that might appear in test scenario descriptions.

    Delegates:
        - self._parse_sections: Parses the test docstring into a dict of named sections
          using the 12 test-specific headings.
        - PLACEHOLDER_RE.search: Detects unfilled placeholders with 3+ chars inside brackets.
        - re.search: Validates `#test-eval:criterion=N` score tag patterns.
        - self.add_message: Reports BLQ920-BLQ923 violations.

    Cohesion:
        All methods serve test docstring validation. `visit_module` is intentionally a no-op.
        `visit_functiondef` contains all the filtering and validation logic. `_parse_sections`
        is the only helper, providing section parsing specific to test documentation headings.
        The constants are all test-documentation-specific.

    Separation:
        - ResponsibilityDocsChecker: Validates architecture documentation for source entities
          with different required sections (8 common + Invariants) and different score criteria
          (#arch-eval tags with 0-5 values). This checker validates test documentation for
          test functions only.
        - QualityGatesChecker: Validates code patterns (including a no-test-class rule); this
          checker validates documentation completeness for test functions.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint visitors: Calls `visit_module` (no-op) and `visit_functiondef`.

    State and side effects:
        None, keeps no persistent state. Each `visit_functiondef` call is stateless.
        Docstrings are extracted from AST nodes via `node.doc_node.value`. Messages emitted
        via `self.add_message()`. No file I/O beyond what astroid performed during parsing.

    Invariants:
        - Only `test_`-prefixed functions in recognized test files are checked.
        - Test file recognition: filename matches `test_*` or `*_test.py`, path contains
          `cases/` or `/tests/` or starts with `tests/`, excluding `conftest.py`,
          `__init__.py`, and `test_pylint_checkers.py`.
        - All 12 required sections must be present (BLQ920).
        - Only "Test scenario" is checked for minimum 30-char length (BLQ921).
        - 4 test quality criteria must have `#test-eval:name=N` tags with N in 1-5 (BLQ922).
        - Placeholder regex requires 3+ chars inside brackets (BLQ923).
        - Module-level validation is explicitly disabled.
        - Functions without a `doc_node` are treated as having no docstring (sections dict
          will be empty, triggering BLQ920 for all sections).

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    name = "test-responsibility-docs"

    msgs = {
        "R9020": (
            "BLQ920: missing test responsibility documentation section: %s",
            "missing-test-responsibility-doc",
            "Test modules must include all required sections in their module-level docstring.",
        ),
        "R9021": (
            "BLQ921: test responsibility or scenario must be descriptive enough: %s",
            "short-test-responsibility-doc",
            "Test responsibility and scenario descriptions must meet the minimum length requirements.",
        ),
        "R9022": (
            "BLQ922: missing or invalid test quality score tag: %s",
            "missing-test-quality-score",
            "Test documentation must include parseable #test-eval tags with values from 1 to 5.",
        ),
        "R9023": (
            "BLQ923: unfilled test responsibility placeholder in section: %s",
            "unfilled-test-responsibility-placeholder",
            "Test template placeholders like <placeholder> must be replaced before commit.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Intentionally disabled for modules.

        Responsibility:
            Intentionally disabled for modules. Returns immediately without performing
            any validation. Module-level test documentation is not enforced by this
            checker — only test function docstrings are validated. This design choice
            reflects that test module docstrings may serve organizational or descriptive
            purposes that don't fit the 12-section test documentation template.

        Reason for existence:
            This method exists as a no-op to satisfy Pylint's visitor interface. Pylint
            calls `visit_module` for every module, and without this method, the parent
            class's default behavior might apply. The explicit no-op documents the
            intentional decision not to validate module-level test documentation.

        Delegates:
            - (none): Immediately returns.

        Cohesion:
            This method does nothing — it is intentionally empty. Its cohesion is
            defined by what it explicitly doesn't do.

        Separation:
            - visit_functiondef: The active validation method; this method is the
              inactive counterpart, making the scope limitation explicit.

        Main consumers:
            - Pylint's module visitor: Called automatically but has no effect.

        State and side effects:
            None. No I/O, no message emission, no state changes.

        Architecture score:
            #arch-eval:reason_for_existence=2
            #arch-eval:owned_responsibility=1
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=3
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """
        Provide the primary validation method for test function documentation.

        Responsibility:
            The primary validation method for test function documentation. First filters
            to only `test_`-prefixed functions in recognized test files (files under
            `cases/` or `/tests/` directories, or starting with `tests/`, with filenames
            starting with `test_` or ending with `_test.py`, excluding `conftest.py`,
            `__init__.py`, and `test_pylint_checkers.py`). For qualifying functions,
            extracts the docstring from `node.doc_node.value`, parses it into sections
            via `_parse_sections`, and runs four checks: (1) verifies all 12 required
            sections are present (BLQ920), (2) checks the Test scenario section meets the
            30-character minimum (BLQ921), (3) verifies all 4 test quality criteria have
            valid `#test-eval:criterion=N` tags (BLQ922), and (4) detects unfilled
            `<...>` placeholders with 3+ characters (BLQ923).

        Reason for existence:
            This method is the sole active validation entry point for test documentation.
            The extensive file-filtering logic ensures the checker only operates on actual
            test functions in actual test files, avoiding false positives on helper
            functions, conftest fixtures, or the checker's own test code. The four
            validation checks are sequenced to report all issues in a single pass rather
            than stopping at the first violation.

        Delegates:
            - self._parse_sections: Parses the docstring into named sections.
            - PLACEHOLDER_RE.search: Detects unfilled placeholders in section content.
            - re.search: Validates `#test-eval:criterion=N` tags.
            - self.add_message: Emits BLQ920-BLQ923 violations.

        Cohesion:
            This method does one thing: validate a test function's docstring. The filtering,
            extraction, parsing, and four validation checks are all sequential steps in this
            single pipeline.

        Separation:
            - visit_module: The no-op counterpart; this method does the actual work.
            - _parse_sections: Handles the parsing; this method handles the business rules.
            - ResponsibilityDocsChecker.visit_functiondef: Validates source function
              docstrings against a different template; this method validates test function
              docstrings.

        Main consumers:
            - Pylint's function visitor: Called automatically for every `FunctionDef` node.

        State and side effects:
            Reads `node.doc_node.value` and `node.root().file` from the AST. Calls
            `self.add_message()` for violations. No file I/O, no state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        if not node.name.startswith("test_"):
            return

        # Get parent module to check if it's a test file
        module = node.root()
        if not isinstance(module, nodes.Module):
            return

        filepath = module.file
        if not filepath:
            return

        normalized = filepath.replace("\\", "/")
        filename = Path(filepath).name
        is_test_file = (
            (filename.startswith("test_") or filename.endswith("_test.py"))
            and ("case/" in normalized or "/tests/" in normalized or normalized.startswith("tests/"))
            and filename not in {"conftest.py", "__init__.py", "test_pylint_checkers.py"}
        )
        if not is_test_file:
            return

        doc = node.doc_node.value if node.doc_node else None
        sections = self._parse_sections(doc)

        for section in REQUIRED_TEST_SECTIONS:
            if not sections.get(section):
                self.add_message(
                    "missing-test-responsibility-doc", node=node, args=(f"function {node.name} -> {section}",)
                )
            elif PLACEHOLDER_RE.search(sections[section]):
                self.add_message(
                    "unfilled-test-responsibility-placeholder", node=node, args=(f"function {node.name} -> {section}",)
                )

        # Verify minimum length for description fields
        for section in ("Test scenario",):
            text = " ".join(sections.get(section, "").split())
            if text and len(text) < MIN_LONG_SECTION:
                self.add_message(
                    "short-test-responsibility-doc", node=node, args=(f"function {node.name} -> {section}",)
                )

        # Check for test evaluation tags
        doc_str = doc or ""
        for criterion in TEST_SCORE_CRITERIA:
            tag_pattern = rf"#test-eval:{criterion}=([1-5])(?:\s|$)"
            if not re.search(tag_pattern, doc_str):
                self.add_message(
                    "missing-test-quality-score", node=node, args=(f"function {node.name} -> {criterion}",)
                )

    def _parse_sections(self, docstring: str | None) -> dict[str, str]:
        """
        Parse a test function's docstring into a dictionary mapping section names to
        their content.

        Responsibility:
            Parses a test function's docstring into a dictionary mapping section names to
            their content. Recognizes the 12 test-specific heading strings (Test target,
            Test type, Test scenario, BDD reference, Fixtures, Mocks, Side effects,
            Reduction, Escalation, Atomicity, Autonomy, Test quality score) each followed
            by a colon. Content lines between headings are accumulated under the preceding
            heading, preserving original line breaks. Lines before the first recognized
            heading are ignored. Content is stripped of leading/trailing whitespace in the
            final dict values. Returns an empty dict if `docstring` is None or empty.

        Reason for existence:
            This method provides the structured representation of a test docstring that the
            checker needs for section-level validation. The heading-based parsing approach
            mirrors `ResponsibilityDocsChecker._parse_sections` but with test-specific
            headings. It exists as a separate method (rather than being shared) because
            the heading set is different and the test documentation template may evolve
            independently of the architecture documentation template.

        Delegates:
            - (none): Pure string processing with no external dependencies.

        Cohesion:
            This method does exactly one thing: parse a test docstring into named sections.
            The heading set, line iteration, accumulation, and stripping are all steps in
            this single parsing pipeline.

        Separation:
            - visit_functiondef: Consumes the parsed sections dict for validation.
            - ResponsibilityDocsChecker._parse_sections: Parses architecture docstrings
              with different headings; this method parses test docstrings.

        Main consumers:
            - TestResponsibilityDocsChecker.visit_functiondef: The sole caller.

        State and side effects:
            None, pure function. Takes a string or None, returns a dict. No I/O, no
            mutations.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if not docstring:
            return {}
        sections: dict[str, list[str]] = {}
        current: str | None = None
        headings = {f"{section}:" for section in REQUIRED_TEST_SECTIONS}
        for raw_line in docstring.splitlines():
            line = raw_line.strip()
            if line in headings:
                current = line[:-1]
                sections[current] = []
            elif current:
                sections[current].append(raw_line)
        return {key: "\n".join(value).strip() for key, value in sections.items()}
