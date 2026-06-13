"""
Validate that all modules, classes, functions, and async functions in non-test source code have
complete responsibil.

Responsibility:
    Validates that all modules, classes, functions, and async functions in non-test source code have
    complete responsibility architecture documentation in their docstrings. Enforces four rules:
    BLQ910 (missing-responsibility-doc) flags missing required sections (Responsibility, Reason for
    existence, Delegates, Cohesion, Separation, Main consumers, State and side effects, Architecture
    score, plus Invariants for modules and classes); BLQ911 (short-responsibility-doc) flags
    Responsibility and Reason for existence sections shorter than 140 characters; BLQ912
    (legacy-responsibility-doc) flags deprecated section names "Not split because" and "Not merged
    with"; BLQ913 (missing-architecture-score) flags missing or malformed `#arch-eval:NAME=VALUE`
    tags for all 9 score criteria; BLQ914 (unfilled-responsibility-placeholder) flags `<...>`
    template placeholders that haven't been replaced with concrete descriptions.

Reason for existence:
    This module is the enforcement mechanism for the project's architecture documentation discipline.
    Every module, class, and function must document its architectural role using a standardized
    template of 8 required sections plus Invariants for stateful entities. The checker ensures
    documentation is not just present but substantive (140+ chars for key sections), free of
    template placeholders, and includes parseable numeric scores. This is not a general-purpose
    docstring linter — it enforces a specific documentation contract unique to pytest-bdd-ng.
    The module uses stdlib `ast` as a fallback for module docstrings that astroid may not expose,
    and regex for placeholder and score-tag detection. It is separate from
    `TestResponsibilityDocsChecker` because test documentation has a different template with
    different sections and score criteria.

Delegates:
    - self._check_node: Central validation method that checks sections, lengths, placeholders,
      legacy names, and score tags for a given AST node.
    - self._doc_for_node: Extracts the docstring from an AST node using astroid's doc_node,
      the `doc` attribute, or stdlib `ast.parse` as a fallback for modules.
    - self._parse_sections: Parses a docstring into a dict of section-name → content by
      recognizing known heading strings followed by colons.
    - ast.parse / ast.get_docstring: Fallback for extracting module docstrings when astroid's
      doc_node is unavailable.
    - re.search / re.compile: Compiles and applies patterns for placeholder and score-tag detection.
    - self.add_message: Reports BLQ910-BLQ914 violations.

Cohesion:
    All logic in this module serves the single purpose of responsibility docstring validation.
    The AST visitors (visit_module, visit_classdef, visit_functiondef, visit_asyncfunctiondef)
    all delegate to `_check_node` with the appropriate `require_invariants` flag. The docstring
    extraction (`_doc_for_node`) and section parsing (`_parse_sections`) are shared infrastructure.
    The constants (`MIN_LONG_SECTION`, `PLACEHOLDER_RE`, `REQUIRED_COMMON_SECTIONS`,
    `SCORE_CRITERIA`) are all used exclusively for docstring validation.

Separation:
    - test_responsibility_docs.py: TestResponsibilityDocsChecker validates test function docstrings
      with a different template (Test target, Test type, Test scenario, etc.) and different score
      criteria (isolation, determinism, setup_complexity, assertions_clarity). The two checkers
      serve different audiences (source code vs test code) with different documentation contracts.
    - quality_gates.py: QualityGatesChecker enforces code patterns; this module enforces
      documentation completeness.
    - noqa_rules.py / typing_rules.py: Enforce comment format; this module enforces docstring content.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `ResponsibilityDocsChecker` into Pylint during plugin
      startup.
    - Pylint visitors: Calls `visit_module`, `visit_classdef`, `visit_functiondef`, and
      `visit_asyncfunctiondef` during AST traversal.
    - CI/CD: Ensures all source entities have complete architecture documentation before merge.

State and side effects:
    None, keeps no persistent state. All methods are stateless — they inspect AST nodes,
    parse docstrings, and emit messages via `self.add_message()`. The `_doc_for_node` method
    may read a module file from disk via `Path.read_text()` as a fallback when astroid's
    doc_node is unavailable, but this is per-call with no caching. The `ast.parse` call
    creates temporary ASTs that are immediately discarded.

Invariants:
    - `MIN_LONG_SECTION` = 140 characters; Responsibility and Reason for existence must meet this.
    - `PLACEHOLDER_RE` matches `<...>` patterns with any content inside angle brackets.
    - `REQUIRED_COMMON_SECTIONS` = 8 sections; all must be present in every docstring.
    - "Invariants" section is required only for modules and classes (not functions/methods).
    - `SCORE_CRITERIA` = 9 criteria; each must have a valid `#arch-eval:name=N` tag where N is 0-5.
    - "Not split because" and "Not merged with" are legacy section names that trigger BLQ912.
    - Test files (under `pytest_bdd_testing/` or `/tests/` or starting with `tests/`) are exempt.
    - Overloaded functions (decorated with `@overload`) are exempt from documentation checks.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

MIN_LONG_SECTION = 140
PLACEHOLDER_RE = re.compile(r"<[A-Z][a-z]")
REQUIRED_COMMON_SECTIONS = (
    "Responsibility",
    "Reason for existence",
    "Delegates",
    "Cohesion",
    "Separation",
    "Main consumers",
    "State and side effects",
    "Architecture score",
)
SCORE_CRITERIA = (
    "reason_for_existence",
    "owned_responsibility",
    "delegation_boundary",
    "cohesion",
    "separation",
    "consumer_clarity",
    "state_invariants",
    "entity_fullness",
    "locational_stability",
)


class ResponsibilityDocsChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that validates architecture responsibility documentation in
    docstrings of modules, classes, fu.

    Responsibility:
        A Pylint `BaseChecker` that validates architecture responsibility documentation in
        docstrings of modules, classes, functions, and async functions across non-test source
        code. For each visited node, extracts the docstring via `_doc_for_node`, parses it into
        named sections via `_parse_sections`, and checks five conditions: (1) all required
        sections are present (BLQ910), (2) Responsibility and Reason for existence meet the
        140-character minimum (BLQ911), (3) no legacy section names "Not split because" or
        "Not merged with" are used (BLQ912), (4) all 9 architecture score criteria have valid
        `#arch-eval:name=N` tags (BLQ913), and (5) no `<...>` template placeholders remain in
        any section content (BLQ914). Skips test files, overloaded functions, and files under
        `pytest_bdd_testing/`, `/tests/`, or starting with `tests/`.

    Reason for existence:
        This checker enforces a documentation discipline that is central to the project's
        architecture governance. Every entity must document its architectural role using a
        standardized template, enabling automated architecture review and ensuring that design
        decisions are captured alongside code. The checker validates both completeness (all
        sections present, scores tagged) and quality (sufficient length, no placeholders, no
        legacy names). It uses astroid's doc_node as the primary docstring source but falls
        back to stdlib `ast` for module docstrings because astroid's doc_node can be None for
        modules in some configurations. The checker is separate from
        `TestResponsibilityDocsChecker` because test documentation follows a completely
        different template with different required sections and score criteria.

    Delegates:
        - self._check_node: Central validation logic shared by all visitor methods.
        - self._doc_for_node: Extracts docstring from astroid node or stdlib AST fallback.
        - self._parse_sections: Parses docstring text into a dict of named sections.
        - ast.parse / ast.get_docstring: Fallback for module-level docstring extraction.
        - PLACEHOLDER_RE.search: Detects unfilled `<...>` template placeholders.
        - re.search: Validates `#arch-eval:name=N` score tag patterns.
        - self.add_message: Reports BLQ910-BLQ914 violations.

    Cohesion:
        Every method in this class serves the single purpose of architecture docstring validation.
        The four visitor methods are thin adapters that call `_check_node` with the appropriate
        flags. The helper methods (`_doc_for_node`, `_parse_sections`) provide the extraction
        and parsing infrastructure. The constants are all docstring-validation-specific.

    Separation:
        - TestResponsibilityDocsChecker: Validates test function docstrings with different
          required sections (`Test target`, `Test type`, etc.) and different score criteria
          (`#test-eval:isolation=N`, etc.). Both validate docstrings but for different
          documentation contracts.
        - QualityGatesChecker: Validates code patterns; unrelated to documentation.
        - NoqaRulesChecker / TypingRulesChecker: Validate comment format; unrelated to docstrings.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint visitors: Calls `visit_module`, `visit_classdef`, `visit_functiondef`,
          `visit_asyncfunctiondef`.

    State and side effects:
        None, keeps no persistent state. Each visitor call is stateless — docstrings are
        extracted and validated without caching. The `_doc_for_node` method may read module
        files from disk via `Path.read_text()` when the stdlib AST fallback is needed, and
        `ast.parse` creates temporary ASTs. Messages are emitted via `self.add_message()`.

    Invariants:
        - 8 required sections for all entities; 9 (including Invariants) for modules and classes.
        - `MIN_LONG_SECTION` = 140; only Responsibility and Reason for existence are checked.
        - `SCORE_CRITERIA` = 9 criteria; score values must be 0-5.
        - `PLACEHOLDER_RE` matches any `<...>` pattern with content inside angle brackets.
        - Test paths are skipped: paths containing `pytest_bdd_testing/`, `/tests/`, or starting
          with `tests/`.
        - Functions decorated with `@overload` are skipped (they are type stubs, not implementations).
        - File path normalization uses forward-slash replacement for cross-platform consistency.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    name = "responsibility-docs"

    msgs = {
        "R9010": (
            "BLQ910: missing responsibility documentation section: %s",
            "missing-responsibility-doc",
            "Module, class, function, and method docstrings must include responsibility architecture sections.",
        ),
        "R9011": (
            "BLQ911: responsibility documentation section is too short: %s",
            "short-responsibility-doc",
            "Responsibility and Reason for existence must be descriptive enough to explain the architecture boundary.",
        ),
        "R9012": (
            "BLQ912: legacy responsibility documentation section used: %s",
            "legacy-responsibility-doc",
            "Use Cohesion and Separation instead of Not split because and Not merged with.",
        ),
        "R9013": (
            "BLQ913: missing or invalid architecture score tag: %s",
            "missing-architecture-score",
            "Responsibility documentation must include parseable #arch-eval tags with integer values from 0 to 5.",
        ),
        "R9014": (
            "BLQ914: unfilled responsibility placeholder in section: %s",
            "unfilled-responsibility-placeholder",
            "Responsibility documentation template placeholders must be replaced before commit.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Validate the module-level docstring for all required architecture documentation
        sections.

        Responsibility:
            Validates the module-level docstring for all required architecture documentation
            sections. Calls `_check_node(node, require_invariants=True)` because modules
            (like classes) must document their invariants. Modules are the top-level
            documentation target and provide context for all nested entities.

        Reason for existence:
            This is the Pylint visitor entry point for module-level docstring validation.
            The `require_invariants=True` flag distinguishes modules from functions/methods,
            which do not require an Invariants section. The method is a thin adapter that
            connects Pylint's module visitor to the shared `_check_node` logic.

        Delegates:
            - self._check_node: Performs all section, length, placeholder, legacy, and score
              validation for the module's docstring.

        Cohesion:
            Single-line delegation. Its only purpose is to invoke `_check_node` with the
            correct invariants flag for modules.

        Separation:
            - visit_classdef: Same delegation pattern with `require_invariants=True`.
            - visit_functiondef / visit_asyncfunctiondef: Same delegation with
              `require_invariants=False`.

        Main consumers:
            - Pylint's module visitor: Called automatically for every module in the linted tree.

        State and side effects:
            Delegates to `_check_node` which may call `self.add_message()`. No direct side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self._check_node(node, require_invariants=True)

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """
        Validate the class-level docstring for all required architecture documentation
        sections.

        Responsibility:
            Validates the class-level docstring for all required architecture documentation
            sections. Calls `_check_node(node, require_invariants=True)` because classes,
            like modules, must document their invariants.

        Reason for existence:
            This is the Pylint visitor entry point for class-level docstring validation.
            Classes are architectural entities that own state and behavior, so they require
            the full documentation template including Invariants.

        Delegates:
            - self._check_node: Performs all validation for the class's docstring.

        Cohesion:
            Single-line delegation with the invariants flag set to True.

        Separation:
            - visit_module: Same delegation pattern; both require invariants.
            - visit_functiondef / visit_asyncfunctiondef: Same delegation but without invariants.

        Main consumers:
            - Pylint's class visitor: Called automatically for every `ClassDef` node.

        State and side effects:
            Delegates to `_check_node` which may call `self.add_message()`. No direct side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self._check_node(node, require_invariants=True)

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """
        Validate function-level docstrings for required architecture documentation sections.

        Responsibility:
            Validates function-level docstrings for required architecture documentation sections.
            Skips overloaded functions (decorated with `@overload`) because they are type stubs,
            not implementations. Calls `_check_node(node, require_invariants=False)` because
            functions do not require an Invariants section.

        Reason for existence:
            This visitor handles synchronous function definitions. The overload check prevents
            false positives on `@typing.overload` decorated functions, which are type
            annotations only and typically don't have full documentation. The
            `require_invariants=False` flag reflects that functions are stateless by nature
            and don't need to document invariants.

        Delegates:
            - self._check_node: Performs all validation for the function's docstring.

        Cohesion:
            Thin adapter: check for overload decorator, then delegate to `_check_node` without
            invariants. The overload check is specific to functions/methods.

        Separation:
            - visit_asyncfunctiondef: Identical logic for async functions; separate because
              Pylint dispatches them to different visitor methods.
            - visit_module / visit_classdef: Same delegation but require invariants.

        Main consumers:
            - Pylint's function visitor: Called automatically for every `FunctionDef` node.

        State and side effects:
            Checks decorator names via `decorator.as_string()`. Delegates to `_check_node`
            which may call `self.add_message()`. No direct side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if node.decorators:
            for decorator in node.decorators.nodes:
                if decorator.as_string().endswith("overload"):
                    return
        self._check_node(node, require_invariants=False)

    def visit_asyncfunctiondef(self, node: nodes.AsyncFunctionDef) -> None:
        """
        Validate async function docstrings for required architecture documentation sections.

        Responsibility:
            Validates async function docstrings for required architecture documentation sections.
            Skips overloaded functions (decorated with `@overload`). Calls
            `_check_node(node, require_invariants=False)` — async functions, like sync functions,
            do not require an Invariants section.

        Reason for existence:
            Pylint dispatches `AsyncFunctionDef` and `FunctionDef` to different visitor methods,
            but the documentation validation logic is identical. This method ensures async
            functions are covered without duplicating the validation pipeline.

        Delegates:
            - self._check_node: Performs all validation for the async function's docstring.

        Cohesion:
            Thin adapter with overload guard, identical to `visit_functiondef`. Its only purpose
            is to ensure async functions are covered by the same validation logic.

        Separation:
            - visit_functiondef: Identical logic for sync functions; separate due to Pylint's
              AST node type dispatch.
            - visit_module / visit_classdef: Same delegation but require invariants.

        Main consumers:
            - Pylint's async function visitor: Called for every `AsyncFunctionDef` node.

        State and side effects:
            Checks decorator names. Delegates to `_check_node`. No direct side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if node.decorators:
            for decorator in node.decorators.nodes:
                if decorator.as_string().endswith("overload"):
                    return
        self._check_node(node, require_invariants=False)

    def _check_node(self, node: nodes.NodeNG, *, require_invariants: bool) -> None:
        """
        Provide the central validation method for architecture responsibility documentation.

        Responsibility:
            The central validation method for architecture responsibility documentation. For a
            given AST node, extracts its docstring via `_doc_for_node`, parses it into named
            sections via `_parse_sections`, and runs five checks: (1) verifies all required
            sections are present — the 8 common sections plus Invariants if `require_invariants`
            is True (BLQ910); (2) checks Responsibility and Reason for existence sections meet
            the 140-character minimum (BLQ911); (3) detects legacy section names "Not split
            because" and "Not merged with" (BLQ912); (4) validates that all 9 score criteria
            have `#arch-eval:name=N` tags with values 0-5 (BLQ913); (5) detects unfilled
            `<...>` template placeholders in any section (BLQ914). Skips test files and nodes
            with no file path.

        Reason for existence:
            This method is the core validation engine shared by all four visitor methods. It
            consolidates what would otherwise be duplicated logic across `visit_module`,
            `visit_classdef`, `visit_functiondef`, and `visit_asyncfunctiondef`. The
            `require_invariants` parameter allows the same method to handle both entity types
            (modules/classes need Invariants, functions don't). The file-path filtering
            prevents validation of test code and files without paths. The method exists at
            this level of abstraction — between the visitors and the extraction/parsing
            helpers — because it orchestrates the full validation pipeline without being tied
            to a specific AST node type.

        Delegates:
            - self._doc_for_node: Extracts the docstring from the AST node.
            - self._parse_sections: Parses the docstring into named sections.
            - PLACEHOLDER_RE.search: Detects unfilled placeholders in section content.
            - re.search: Validates score tag patterns for each criterion.
            - self.add_message: Emits BLQ910-BLQ914 diagnostics.

        Cohesion:
            This method orchestrates the five documentation checks in a clear sequence. Each
            check is independent of the others, but they all operate on the same parsed sections
            dict. The method itself contains no extraction or parsing logic — it only iterates
            over requirements and sections to find violations.

        Separation:
            - _doc_for_node / _parse_sections: These handle extraction and parsing; this method
              handles the business rules (what's required, what's too short, what's legacy).
            - Visitor methods: These handle dispatch and entity-type decisions (overload guard,
              invariants flag); this method handles the actual validation.

        Main consumers:
            - visit_module, visit_classdef, visit_functiondef, visit_asyncfunctiondef: All four
              visitors delegate to this method.

        State and side effects:
            May trigger `_doc_for_node` which can read a file from disk (for module fallback).
            Calls `self.add_message()` for violations. No persistent state changes.

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
        filepath = node.root().file
        if filepath:
            normalized_path = filepath.replace("\\", "/")
            if (
                "pytest_bdd_testing/" in normalized_path
                or "/tests/" in normalized_path
                or normalized_path.startswith("tests/")
            ):
                return

        doc = self._doc_for_node(node)
        sections = self._parse_sections(doc)
        required = list(REQUIRED_COMMON_SECTIONS)
        if require_invariants:
            required.append("Invariants")
        for section in required:
            if not sections.get(section):
                self.add_message("missing-responsibility-doc", node=node, args=(section,))
            elif PLACEHOLDER_RE.search(sections[section]):
                self.add_message("unfilled-responsibility-placeholder", node=node, args=(section,))
        for section in ("Responsibility", "Reason for existence"):
            text = " ".join(sections.get(section, "").split())
            if text and len(text) < MIN_LONG_SECTION:
                self.add_message("short-responsibility-doc", node=node, args=(section,))
        for legacy in ("Not split because", "Not merged with"):
            if legacy in sections:
                self.add_message("legacy-responsibility-doc", node=node, args=(legacy,))
        for criterion in SCORE_CRITERIA:
            tag_pattern = rf"#arch-eval:{criterion}=([0-5])(?:\s|$)"
            if not re.search(tag_pattern, doc):
                self.add_message("missing-architecture-score", node=node, args=(criterion,))

    def _doc_for_node(self, node: nodes.NodeNG) -> str:
        """
        Extract the docstring from an AST node using a three-tier fallback strategy.

        Responsibility:
            Extracts the docstring from an AST node using a three-tier fallback strategy.
            First, tries `node.doc_node.value` (astroid's structured doc node). If unavailable,
            tries `node.doc` (the string doc attribute). For `Module` nodes specifically, if
            both astroid approaches fail, falls back to stdlib `ast.parse` to read and parse
            the file from disk, then uses `ast.get_docstring()` to extract the module docstring.
            Returns an empty string if all approaches fail or the file is unreadable.

        Reason for existence:
            This method exists because astroid's docstring handling is inconsistent across
            Python versions and configurations — `node.doc_node` can be `None` for modules
            even when a docstring exists. The stdlib `ast` module provides a reliable fallback
            for module-level docstrings. The three-tier strategy ensures docstrings are found
            in the maximum number of cases. This method is separate from `_check_node` to keep
            the extraction concern isolated from the validation concern.

        Delegates:
            - ast.parse: Parses the module file from disk as a stdlib AST.
            - ast.get_docstring: Extracts the docstring from a stdlib AST module node.
            - Path.read_text: Reads the module file from disk for the stdlib AST fallback.

        Cohesion:
            This method does exactly one thing: get the docstring for a node. The three-tier
            strategy is a single concern — "find the docstring by whatever means available."

        Separation:
            - _parse_sections: Takes the string this method returns and parses it into sections.
            - _check_node: Takes the parsed sections and validates them. This method is the
              first step in the pipeline.

        Main consumers:
            - ResponsibilityDocsChecker._check_node: The sole caller.

        State and side effects:
            May read a module file from disk via `Path.read_text()` and `ast.parse()` in the
            stdlib fallback path. Handles OSError, SyntaxError, and UnicodeDecodeError
            gracefully by returning "". No caching or persistent state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        doc_node = getattr(node, "doc_node", None)
        if doc_node is not None and getattr(doc_node, "value", None):
            return str(doc_node.value)
        doc = getattr(node, "doc", None)
        if doc:
            return str(doc)
        if isinstance(node, nodes.Module) and node.file:
            try:
                tree = ast.parse(Path(node.file).read_text(encoding="utf-8"), filename=node.file)
            except (OSError, SyntaxError, UnicodeDecodeError):
                return ""
            return ast.get_docstring(tree) or ""
        return ""

    def _parse_sections(self, doc: str) -> dict[str, str]:
        """
        Parse a raw docstring into a dictionary mapping section names to their content.

        Responsibility:
            Parses a raw docstring into a dictionary mapping section names to their content.
            Recognizes 12 known heading strings (ending with colons): Responsibility, Reason
            for existence, Delegates, Cohesion, Separation, Main consumers, State and side
            effects, Invariants, Failure semantics, Architecture score, Not split because,
            and Not merged with. Content between headings is accumulated (preserving original
            line breaks) and associated with the preceding heading. Lines before the first
            heading are ignored. Content is stripped of leading/trailing whitespace in the
            final dict values.

        Reason for existence:
            This method provides the structured representation of a free-form docstring that
            `_check_node` needs for validation. The heading-based parsing approach is used
            because the documentation template uses colon-terminated headings as section
            delimiters, not indentation or markup. The method handles multi-line section
            content by accumulating lines under the current heading until the next heading
            is encountered. It is separate from `_check_node` to keep parsing logic isolated
            from validation logic.

        Delegates:
            - (none): Pure string processing with no external dependencies.

        Cohesion:
            This method does one thing: parse a docstring into sections. The heading detection,
            line accumulation, and content stripping are all steps in this single parsing
            pipeline.

        Separation:
            - _doc_for_node: Provides the raw docstring; this method structures it.
            - _check_node: Consumes the structured sections dict; this method produces it.

        Main consumers:
            - ResponsibilityDocsChecker._check_node: The sole caller.

        State and side effects:
            None, pure function. Takes a string, returns a dict. No I/O, no mutations.

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
        headings = {
            "Responsibility:",
            "Reason for existence:",
            "Delegates:",
            "Cohesion:",
            "Separation:",
            "Main consumers:",
            "State and side effects:",
            "Invariants:",
            "Failure semantics:",
            "Architecture score:",
            "Not split because:",
            "Not merged with:",
        }
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for raw_line in doc.splitlines():
            line = raw_line.strip()
            if line in headings:
                current = line[:-1]
                sections[current] = []
            elif current:
                sections[current].append(raw_line)
        return {key: "\n".join(value).strip() for key, value in sections.items()}
