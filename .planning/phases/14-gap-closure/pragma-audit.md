# Phase 14 Pragma Audit

Generated: 2026-05-20

Command:

```bash
rg "# pragma: no cover" src/pytest_bdd/ -n
```

## Summary

- Total instances found: 38
- KEEP: 38
- REMOVE: 0

No unjustified reachable pragmas were removed. The remaining instances are abstract protocol methods, abstract base method guards, type-checking/import guards, compatibility fallbacks, script entrypoints, optional plugin paths, or defensive branches that require external/runtime error states.

## Catalog

| File:line | Action | Justification |
|---|---|---|
| `src/pytest_bdd/__init__.py:43` | KEEP | TYPE_CHECKING import block; runtime-unreachable. |
| `src/pytest_bdd/tag_expression.py:26` | KEEP | Protocol abstract parse method. |
| `src/pytest_bdd/tag_expression.py:36` | KEEP | Protocol abstract evaluate method. |
| `src/pytest_bdd/hook.py:207` | KEEP | Defensive hook-resolution fallback branch. |
| `src/pytest_bdd/scenario_locator.py:57` | KEEP | Protocol method declaration. |
| `src/pytest_bdd/scenario_locator.py:66` | KEEP | Observer protocol callback declaration. |
| `src/pytest_bdd/scenario_locator.py:70` | KEEP | Observer protocol callback declaration. |
| `src/pytest_bdd/scenario_locator.py:74` | KEEP | Observer protocol callback declaration. |
| `src/pytest_bdd/scenario_locator.py:90` | KEEP | Resolver protocol method declaration. |
| `src/pytest_bdd/script/validate_feature_headings.py:213` | KEEP | Parser-level defensive failure path. |
| `src/pytest_bdd/script/validate_feature_headings.py:424` | KEEP | Script `__main__` guard. |
| `src/pytest_bdd/util/data_table.py:7` | KEEP | TYPE_CHECKING import block. |
| `src/pytest_bdd/util/toolz_test.py:10` | KEEP | TYPE_CHECKING import block. |
| `src/pytest_bdd/compatibility/parser.py:37` | KEEP | Parser protocol method declaration. |
| `src/pytest_bdd/types/failure_reasons.py:7` | KEEP | Python < 3.11 compatibility fallback. |
| `src/pytest_bdd/util/other.py:53` | KEEP | Protocol method declaration. |
| `src/pytest_bdd/plugin/struct_bdd/model_builder.py:37` | KEEP | Abstract builder protocol method. |
| `src/pytest_bdd/compatibility/pytest/__init__.py:82` | KEEP | TYPE_CHECKING import block. |
| `src/pytest_bdd/parser.py:31` | KEEP | Optional StructBDD import guard. |
| `src/pytest_bdd/parser.py:86` | KEEP | Defensive hook emitter failure guard. |
| `src/pytest_bdd/parsers.py:69` | KEEP | StepParserProtocol abstract method. |
| `src/pytest_bdd/parsers.py:74` | KEEP | StepParserProtocol abstract property. |
| `src/pytest_bdd/parsers.py:78` | KEEP | StepParserProtocol abstract method. |
| `src/pytest_bdd/parsers.py:82` | KEEP | StepParserProtocol abstract method. |
| `src/pytest_bdd/parsers.py:109` | KEEP | StepParser abstract method. |
| `src/pytest_bdd/parsers.py:115` | KEEP | StepParser abstract property. |
| `src/pytest_bdd/parsers.py:120` | KEEP | StepParser abstract method. |
| `src/pytest_bdd/parsers.py:125` | KEEP | StepParser abstract method. |
| `src/pytest_bdd/parsers.py:170` | KEEP | Regex singledispatch abstract fallback. |
| `src/pytest_bdd/parsers.py:284` | KEEP | Parser constructor invalid-type guard. |
| `src/pytest_bdd/parsers.py:543` | KEEP | Cucumber expression singledispatch abstract fallback. |
| `src/pytest_bdd/parsers.py:591` | KEEP | Cucumber regex singledispatch abstract fallback. |
| `src/pytest_bdd/parsers.py:688` | KEEP | Defensive heuristic parser fallback. |
| `src/pytest_bdd/plugin/cucumber_json/entrypoint.py:10` | KEEP | TYPE_CHECKING import block. |
| `src/pytest_bdd/script/bdd_tree_to_rst.py:524` | KEEP | CLI main wrapper. |
| `src/pytest_bdd/script/bdd_tree_to_rst.py:567` | KEEP | Script `__main__` guard. |
| `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py:88` | KEEP | Runtime transport defensive exception path. |
| `src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py:82` | KEEP | Defensive attachment branch. |
