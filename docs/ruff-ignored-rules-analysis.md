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
| D105 | Magic methods lacked docstrings. | Added short docstrings to `__str__`, `__next__`, `__iter__`, `__eq__`, `__missing__`, and attrs post-init methods. |
| D106 | Public nested classes lacked docstrings. | Added short docstrings to nested option enums, protocols, registries, routes, and locators. |
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
| PLW0603 | Message validation cached schema validator state through a module global. | Replaced mutable global assignment with a cached function. |
| PLW2901 | Loop variables were reassigned inside their loop bodies. | Introduced separate local names. |
| PLW3201 | A private helper used a non-standard dunder-style name. | Renamed it to a normal private helper. |
| Q000 | No current violations remained after formatting. | Removed stale ignore. |
| PLR0904 | Two broad API classes exceed the public-method threshold. | Enabled the rule globally and added targeted per-file legacy exceptions with rationale. |
| TD004 | Some TODO comments omitted the required colon after `TODO`. | Normalized TODO comment punctuation. |
| PLR0911, PLR0912, PLR0914, PLR0915, PLR1702 | Existing complexity hotspots exceed return, branch, local, statement, or nesting thresholds. | Enabled the rules globally and added targeted per-file legacy exceptions with rationale. |
| PLR0913, PLR0917 | Existing public APIs and hook implementations exceed argument-count thresholds. | Enabled the rules globally and added targeted per-file legacy exceptions for current API/protocol shapes. |
| PLR2004 | Existing parsing and protocol code compares against compact arity/version literals. | Enabled the rule globally and added targeted per-file legacy exceptions with rationale. |
| PLC2701 | Compatibility and hook integration modules import pytest private names. | Enabled the rule globally and added targeted per-file exceptions where private pytest APIs are the integration boundary. |

## Remaining ignored rules

Counts below come from `uv run --extra test ruff check src tests docs --isolated --preview --target-version py310 --line-length 120 --select <RULE> --output-format json`. They intentionally measure the raw rule surface, independent of the current project ignore list.

| Rule | Count | Root cause | Why it was not enabled now |
| --- | ---: | --- | --- |
| COM812 | 369 | Formatter and comma lint disagree on multiline trailing comma placement. | Ruff documents this as formatter interference; enabling it would create churn without stronger style guarantees. |
| CPY001 | 334 | Repository files do not carry per-file copyright headers. | Needs a project policy decision and likely generated header strategy. |
| D100-D104, D107 | 1,865 total | Public modules, classes, methods, functions, packages, and `__init__` methods lack docstrings. | Requires documentation policy and broad authoring work, not mechanical cleanup. |
| D212 | 42 | The project currently follows the opposite multi-line docstring convention, enforced by active D213. | Conflicts with the active convention; enabling D212 would require disabling D213 and flipping docstring style. |
| DOC201 | 83 | Docstrings omit return sections. | Requires validating public API return contracts, not just adding boilerplate. |
| FIX002, TD002, TD003 | 42 total | TODO comments lack the stricter task metadata required by flake8-todos. | Needs an issue-tracking convention for author and links before enforcement. |
| PLC0415 | 66 | Imports are intentionally inside functions/hooks to avoid optional dependencies, pytest plugin side effects, or cycles. | Needs dependency-boundary review before moving imports. |
| SLF001 | 207 | Tests and compatibility layers access private members. | Many accesses are deliberate white-box tests or compatibility shims; needs API boundary decisions. |
| PLR6301 | 104 | Many instance methods do not use `self`. | Some methods are protocol hooks, extension points, or intentionally instance-shaped APIs. |
| TC006 | 206 | Runtime `typing.cast` calls use stringified types. | Kept for the documented PyCharm cast-string behavior in the existing config comment. |
