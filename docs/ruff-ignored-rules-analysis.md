# Ruff Ignored Rules Root Cause Analysis

Generated on 2026-05-07 after enabling the low-count mechanical rules that were safe to fix in this pass.

## Enabled in this pass

The following rules were removed from `tool.ruff.lint.ignore` and the reported violations were fixed:

| Rule | Root cause | Resolution |
| --- | --- | --- |
| D205 | A few multi-line docstrings mixed summary text and body text without the required blank separator. | Added summary/body separation. |
| D400, D415 | Docstring summaries had inconsistent terminal punctuation. | Added terminal punctuation to production/docstring surfaces covered by the configured ruff run. |
| D401 | Hook/spec docstrings used declarative wording instead of imperative wording. | Reworded summaries to imperative mood without changing API meaning. |
| D404 | Tutorial module docstring started with `This`. | Reworded the docstring summary. |
| DOC402 | Generator docstrings did not describe yielded values. | Added `Yields` sections. |
| DOC501 | Docstrings omitted exception documentation for direct raises. | Added concise `Raises` sections. |
| E501 | Some lines exceeded the configured 120-character limit. | Wrapped comments, messages, generated markdown rows, and embedded test snippets. |
| PLC0207 | A string split call asked for more splits than the code consumed. | Let ruff simplify the split. |
| PLC1901 | Empty-string comparisons were used where truthiness was equivalent. | Replaced with truthiness checks. |
| PLR0402 | Some module imports used aliases where direct `from ... import ...` is clearer. | Let ruff rewrite direct imports. |
| PLR6201 | Literal tuple membership checks used tuple literals where set literals are preferred. | Replaced membership literals with sets. |
| PLW0108 | Lambda wrappers only forwarded to another callable. | Replaced with direct callables or named helpers. |
| PLW1510 | `subprocess.run` calls intentionally inspected return codes but did not say so. | Added explicit `check=False`. |
| PLW1514 | File opens/read calls omitted explicit encoding. | Added explicit text encodings. |
| PLW1641 | A test helper defined equality without declaring hash behavior. | Marked the helper explicitly unhashable. |
| PLW2901 | Loop variables were reassigned inside their loop bodies. | Introduced separate local names. |
| PLW3201 | A private helper used a non-standard dunder-style name. | Renamed it to a normal private helper. |
| Q000 | No current violations remained after formatting. | Removed stale ignore. |

## Remaining ignored rules

Counts below come from `uv run --extra test ruff check src tests docs --isolated --preview --target-version py310 --line-length 120 --select <RULE> --output-format json`. They intentionally measure the raw rule surface, independent of the current project ignore list.

| Rule | Count | Root cause | Why it was not enabled now |
| --- | ---: | --- | --- |
| COM812 | 369 | Formatter and comma lint disagree on multiline trailing comma placement. | Ruff documents this as formatter interference; enabling it would create churn without stronger style guarantees. |
| CPY001 | 334 | Repository files do not carry per-file copyright headers. | Needs a project policy decision and likely generated header strategy. |
| D100-D107 | 1,897 total | Public modules, classes, methods, functions, packages, nested classes, magic methods, and `__init__` methods lack docstrings. | Requires documentation policy and broad authoring work, not mechanical cleanup. |
| D212 | 41 | The project currently follows the opposite multi-line docstring convention, enforced by active D213. | Conflicts with the active convention; enabling D212 would require disabling D213 and flipping docstring style. |
| DOC201 | 73 | Docstrings omit return sections. | Requires validating public API return contracts, not just adding boilerplate. |
| FIX002, TD002, TD003, TD004 | 51 total | TODO comments lack the stricter task metadata required by flake8-todos. | Needs an issue-tracking convention for author and links before enforcement. |
| PLC0415 | 66 | Imports are intentionally inside functions/hooks to avoid optional dependencies, pytest plugin side effects, or cycles. | Needs dependency-boundary review before moving imports. |
| PLC2701, SLF001 | 238 total | Tests and compatibility layers access private names. | Many accesses are deliberate white-box tests or compatibility shims; needs API boundary decisions. |
| PLR0904 | 2 | Large protocol/base classes expose many public methods. | Structural API shape, not a local lint fix. |
| PLR0911-PLR0917, PLR1702 | 79 total | Complex parser/plugin functions have many returns, branches, arguments, locals, statements, or nesting. | Requires behavior-preserving refactors with targeted tests. |
| PLR2004 | 55 | Tests and protocol code compare against literal values directly. | Needs constants only where they improve meaning; mechanical constants can reduce clarity. |
| PLR6301 | 104 | Many instance methods do not use `self`. | Some methods are protocol hooks, extension points, or intentionally instance-shaped APIs. |
| PLW0603 | 1 | Message validation keeps cached validator state in a module global. | Should be redesigned around an explicit cache object or lazy singleton before enabling. |
| TC006 | 206 | Runtime `typing.cast` calls use stringified types. | Kept for the documented PyCharm cast-string behavior in the existing config comment. |
