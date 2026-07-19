# Phase 35 Strict Source Inventory

## Authority and completion rule

This is the exact D-01/D-02/D-09 ledger. It derives from `git ls-files 'src/pytest_bdd/**/*.py' 'src/pytest_bdd_toolchain/**/*.py' | sort`; every source module appears exactly once. Plan 01 records the no-bypass baseline only in the separate `35-TYPING-BASELINE.md`; it never writes this canonical ledger. Each remediation plan (02–137) owns no more than five modules and writes its own `35-TYPING-EVIDENCE/35-NN.md` record. Plan 140 alone aggregates those records into this shared ledger and runs the full-source zero-error gate.

`status` begins as `baseline pending`; Plan 140 sets it to `clean` only after matching isolated evidence and focused strict-mypy success. The only valid dispositions are `fixed in code`, `local typed boundary added`, and `upstream typed dependency adopted`. No broad bypass or unresolved suppression is allowed.

| module | owner plan | focused command | status | finding disposition | isolated evidence |
|---|---|---|---|---|---|
| `src/pytest_bdd/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_gherkin_go/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_gherkin_go/_bridge.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_gherkin_go/_build.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_gherkin_go/_types.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/file_size_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/init_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/layer_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/noqa_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/plugin_patterns.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/quality_gates.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/responsibility_docs.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/test_import_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/test_responsibility_docs.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/_pylint/checkers/typing_rules.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/collector.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/collector_batch.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/compatibility/enum.py` | 35-02 | `35-02 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-02.md` |
| `src/pytest_bdd/compatibility/importlib/metadata.py` | 35-02 | `35-02 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-02.md` |
| `src/pytest_bdd/compatibility/importlib/resources.py` | 35-02 | `35-02 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-02.md` |
| `src/pytest_bdd/compatibility/parser.py` | 35-02 | `35-02 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-02.md` |
| `src/pytest_bdd/compatibility/path.py` | 35-02 | `35-02 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-02.md` |
| `src/pytest_bdd/compatibility/pathlib.py` | 35-03 | `35-03 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-03.md` |
| `src/pytest_bdd/compatibility/pytest.py` | 35-03 | `35-03 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-03.md` |
| `src/pytest_bdd/compatibility/pytest/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/compatibility/pytest/outcomes.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/compatibility/runtime_compat.py` | 35-03 | `35-03 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-03.md` |
| `src/pytest_bdd/compatibility/struct_bdd.py` | 35-03 | `35-03 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-03.md` |
| `src/pytest_bdd/compatibility/sys.py` | 35-03 | `35-03 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-03.md` |
| `src/pytest_bdd/compatibility/tomllib.py` | 35-04 | `35-04 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-04.md` |
| `src/pytest_bdd/compatibility/typing.py` | 35-04 | `35-04 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-04.md` |
| `src/pytest_bdd/const.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/feature_locator.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/gherkin_go/__init__.py` | 35-04 | `35-04 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-04.md` |
| `src/pytest_bdd/gherkin_go/_bridge.py` | 35-04 | `35-04 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-04.md` |
| `src/pytest_bdd/gherkin_go/_build.py` | 35-04 | `35-04 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-04.md` |
| `src/pytest_bdd/gherkin_go/_types.py` | 35-05 | `35-05 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-05.md` |
| `src/pytest_bdd/hook.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/message_stream_validation/__init__.py` | 35-05 | `35-05 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-05.md` |
| `src/pytest_bdd/message_stream_validation/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/message_stream_validation/pipeline.py` | 35-05 | `35-05 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-05.md` |
| `src/pytest_bdd/message_stream_validation/status.py` | 35-05 | `35-05 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-05.md` |
| `src/pytest_bdd/mimetype.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/__init__.py` | 35-05 | `35-05 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-05.md` |
| `src/pytest_bdd/model/coverage/inventory.py` | 35-06 | `35-06 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-06.md` |
| `src/pytest_bdd/model/coverage/tracker.py` | 35-06 | `35-06 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-06.md` |
| `src/pytest_bdd/model/cucumber_formatter_adapter.py` | 35-06 | `35-06 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-06.md` |
| `src/pytest_bdd/model/cucumber_formatter_contract.py` | 35-06 | `35-06 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-06.md` |
| `src/pytest_bdd/model/execution_message_adapter.py` | 35-06 | `35-06 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-06.md` |
| `src/pytest_bdd/model/execution_message_reader.py` | 35-07 | `35-07 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-07.md` |
| `src/pytest_bdd/model/feature_binding.py` | 35-07 | `35-07 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-07.md` |
| `src/pytest_bdd/model/heading_validation.py` | 35-07 | `35-07 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-07.md` |
| `src/pytest_bdd/model/message_baseline_diff.py` | 35-07 | `35-07 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-07.md` |
| `src/pytest_bdd/model/message_capability.py` | 35-07 | `35-07 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-07.md` |
| `src/pytest_bdd/model/message_capability_inventory.py` | 35-08 | `35-08 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-08.md` |
| `src/pytest_bdd/model/message_consolidation.py` | 35-08 | `35-08 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-08.md` |
| `src/pytest_bdd/model/message_converter.py` | 35-08 | `35-08 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-08.md` |
| `src/pytest_bdd/model/message_extension.py` | 35-08 | `35-08 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-08.md` |
| `src/pytest_bdd/model/message_governance_checklist.py` | 35-08 | `35-08 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-08.md` |
| `src/pytest_bdd/model/message_outcome_mapping.py` | 35-09 | `35-09 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-09.md` |
| `src/pytest_bdd/model/message_registry.py` | 35-09 | `35-09 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-09.md` |
| `src/pytest_bdd/model/message_schema_validation.py` | 35-09 | `35-09 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-09.md` |
| `src/pytest_bdd/model/message_serialization.py` | 35-09 | `35-09 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-09.md` |
| `src/pytest_bdd/model/message_status_governance.py` | 35-09 | `35-09 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-09.md` |
| `src/pytest_bdd/model/message_stream_validation.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/message_transport.py` | 35-10 | `35-10 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-10.md` |
| `src/pytest_bdd/model/message_validation.py` | 35-10 | `35-10 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-10.md` |
| `src/pytest_bdd/model/message_validation_result.py` | 35-10 | `35-10 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-10.md` |
| `src/pytest_bdd/model/message_validation_xdist.py` | 35-10 | `35-10 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-10.md` |
| `src/pytest_bdd/model/run/__init__.py` | 35-10 | `35-10 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-10.md` |
| `src/pytest_bdd/model/run/lifecycle/__init__.py` | 35-11 | `35-11 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-11.md` |
| `src/pytest_bdd/model/run/lifecycle/_run.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/run/lifecycle/_snapshots.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/run/lifecycle/_states.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/run/lifecycle/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/model/run/lifecycle/run.py` | 35-11 | `35-11 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-11.md` |
| `src/pytest_bdd/model/run/lifecycle/snapshots.py` | 35-11 | `35-11 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-11.md` |
| `src/pytest_bdd/model/run/lifecycle/states.py` | 35-11 | `35-11 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-11.md` |
| `src/pytest_bdd/model/run/refs.py` | 35-11 | `35-11 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-11.md` |
| `src/pytest_bdd/model/run/stages.py` | 35-12 | `35-12 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-12.md` |
| `src/pytest_bdd/model/run/transitions.py` | 35-12 | `35-12 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-12.md` |
| `src/pytest_bdd/model/run_access.py` | 35-12 | `35-12 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-12.md` |
| `src/pytest_bdd/model/scenario_collection.py` | 35-12 | `35-12 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-12.md` |
| `src/pytest_bdd/model/scenario_report.py` | 35-12 | `35-12 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-12.md` |
| `src/pytest_bdd/model/scenario_run.py` | 35-13 | `35-13 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-13.md` |
| `src/pytest_bdd/model/stash_access.py` | 35-13 | `35-13 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-13.md` |
| `src/pytest_bdd/parser.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/parsers.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/parsers/__init__.py` | 35-13 | `35-13 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-13.md` |
| `src/pytest_bdd/parsers/base.py` | 35-13 | `35-13 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-13.md` |
| `src/pytest_bdd/parsers/cucumber_expression.py` | 35-13 | `35-13 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-13.md` |
| `src/pytest_bdd/parsers/cucumber_regex.py` | 35-14 | `35-14 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-14.md` |
| `src/pytest_bdd/parsers/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/parsers/heuristic.py` | 35-14 | `35-14 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-14.md` |
| `src/pytest_bdd/parsers/parse_parser.py` | 35-14 | `35-14 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-14.md` |
| `src/pytest_bdd/parsers/re_parser.py` | 35-14 | `35-14 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-14.md` |
| `src/pytest_bdd/parsers/string_parser.py` | 35-14 | `35-14 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-14.md` |
| `src/pytest_bdd/plugin/allure_formatter/__init__.py` | 35-15 | `35-15 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-15.md` |
| `src/pytest_bdd/plugin/allure_formatter/adapter.py` | 35-15 | `35-15 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-15.md` |
| `src/pytest_bdd/plugin/allure_formatter/api_hooks.py` | 35-15 | `35-15 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-15.md` |
| `src/pytest_bdd/plugin/allure_formatter/cli.py` | 35-15 | `35-15 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-15.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/__init__.py` | 35-15 | `35-15 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-15.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/collector.py` | 35-16 | `35-16 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-16.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/converter.py` | 35-16 | `35-16 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-16.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/emitter.py` | 35-16 | `35-16 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-16.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/mapper.py` | 35-16 | `35-16 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-16.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/model.py` | 35-16 | `35-16 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-16.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/reader.py` | 35-17 | `35-17 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-17.md` |
| `src/pytest_bdd/plugin/allure_formatter/converter/step_tree.py` | 35-17 | `35-17 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-17.md` |
| `src/pytest_bdd/plugin/allure_formatter/entrypoint.py` | 35-17 | `35-17 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-17.md` |
| `src/pytest_bdd/plugin/allure_formatter/hook.py` | 35-17 | `35-17 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-17.md` |
| `src/pytest_bdd/plugin/allure_formatter/listener.py` | 35-17 | `35-17 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-17.md` |
| `src/pytest_bdd/plugin/allure_formatter/message_adapter.py` | 35-18 | `35-18 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-18.md` |
| `src/pytest_bdd/plugin/allure_formatter/plugin.py` | 35-18 | `35-18 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-18.md` |
| `src/pytest_bdd/plugin/code_generator/collection.py` | 35-18 | `35-18 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-18.md` |
| `src/pytest_bdd/plugin/code_generator/const.py` | 35-18 | `35-18 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-18.md` |
| `src/pytest_bdd/plugin/code_generator/entrypoint.py` | 35-18 | `35-18 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-18.md` |
| `src/pytest_bdd/plugin/code_generator/events.py` | 35-19 | `35-19 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-19.md` |
| `src/pytest_bdd/plugin/code_generator/hook.py` | 35-19 | `35-19 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-19.md` |
| `src/pytest_bdd/plugin/code_generator/plugin.py` | 35-19 | `35-19 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-19.md` |
| `src/pytest_bdd/plugin/code_generator/rendering.py` | 35-19 | `35-19 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-19.md` |
| `src/pytest_bdd/plugin/code_generator/request.py` | 35-19 | `35-19 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-19.md` |
| `src/pytest_bdd/plugin/code_generator/rewrite.py` | 35-20 | `35-20 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-20.md` |
| `src/pytest_bdd/plugin/cucumber_json/const.py` | 35-20 | `35-20 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-20.md` |
| `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` | 35-20 | `35-20 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-20.md` |
| `src/pytest_bdd/plugin/cucumber_json/hook.py` | 35-20 | `35-20 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-20.md` |
| `src/pytest_bdd/plugin/cucumber_json/model.py` | 35-20 | `35-20 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-20.md` |
| `src/pytest_bdd/plugin/cucumber_json/plugin.py` | 35-21 | `35-21 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-21.md` |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/__init__.py` | 35-21 | `35-21 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-21.md` |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/const.py` | 35-21 | `35-21 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-21.md` |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py` | 35-21 | `35-21 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-21.md` |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/hook.py` | 35-21 | `35-21 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-21.md` |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/plugin.py` | 35-22 | `35-22 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-22.md` |
| `src/pytest_bdd/plugin/cucumber_json_formatter/entrypoint.py` | 35-22 | `35-22 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-22.md` |
| `src/pytest_bdd/plugin/cucumber_json_formatter/hook.py` | 35-22 | `35-22 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-22.md` |
| `src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py` | 35-22 | `35-22 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-22.md` |
| `src/pytest_bdd/plugin/cucumber_junit/entrypoint.py` | 35-22 | `35-22 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-22.md` |
| `src/pytest_bdd/plugin/cucumber_junit/hook.py` | 35-23 | `35-23 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-23.md` |
| `src/pytest_bdd/plugin/cucumber_junit/plugin.py` | 35-23 | `35-23 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-23.md` |
| `src/pytest_bdd/plugin/cucumber_pretty/entrypoint.py` | 35-23 | `35-23 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-23.md` |
| `src/pytest_bdd/plugin/cucumber_pretty/hook.py` | 35-23 | `35-23 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-23.md` |
| `src/pytest_bdd/plugin/cucumber_pretty/plugin.py` | 35-23 | `35-23 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-23.md` |
| `src/pytest_bdd/plugin/cucumber_progress/entrypoint.py` | 35-24 | `35-24 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-24.md` |
| `src/pytest_bdd/plugin/cucumber_progress/hook.py` | 35-24 | `35-24 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-24.md` |
| `src/pytest_bdd/plugin/cucumber_progress/plugin.py` | 35-24 | `35-24 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-24.md` |
| `src/pytest_bdd/plugin/cucumber_progress_bar/entrypoint.py` | 35-24 | `35-24 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-24.md` |
| `src/pytest_bdd/plugin/cucumber_progress_bar/hook.py` | 35-24 | `35-24 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-24.md` |
| `src/pytest_bdd/plugin/cucumber_progress_bar/plugin.py` | 35-25 | `35-25 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-25.md` |
| `src/pytest_bdd/plugin/cucumber_snippets/entrypoint.py` | 35-25 | `35-25 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-25.md` |
| `src/pytest_bdd/plugin/cucumber_snippets/hook.py` | 35-25 | `35-25 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-25.md` |
| `src/pytest_bdd/plugin/cucumber_snippets/plugin.py` | 35-25 | `35-25 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-25.md` |
| `src/pytest_bdd/plugin/cucumber_summary/entrypoint.py` | 35-25 | `35-25 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-25.md` |
| `src/pytest_bdd/plugin/cucumber_summary/hook.py` | 35-26 | `35-26 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-26.md` |
| `src/pytest_bdd/plugin/cucumber_summary/plugin.py` | 35-26 | `35-26 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-26.md` |
| `src/pytest_bdd/plugin/cucumber_usage/entrypoint.py` | 35-26 | `35-26 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-26.md` |
| `src/pytest_bdd/plugin/cucumber_usage/hook.py` | 35-26 | `35-26 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-26.md` |
| `src/pytest_bdd/plugin/cucumber_usage/plugin.py` | 35-26 | `35-26 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-26.md` |
| `src/pytest_bdd/plugin/cucumber_usage_json/entrypoint.py` | 35-27 | `35-27 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-27.md` |
| `src/pytest_bdd/plugin/cucumber_usage_json/hook.py` | 35-27 | `35-27 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-27.md` |
| `src/pytest_bdd/plugin/cucumber_usage_json/plugin.py` | 35-27 | `35-27 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-27.md` |
| `src/pytest_bdd/plugin/debug_mcp/artifacts.py` | 35-27 | `35-27 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-27.md` |
| `src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py` | 35-27 | `35-27 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-27.md` |
| `src/pytest_bdd/plugin/debug_mcp/discovery.py` | 35-28 | `35-28 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-28.md` |
| `src/pytest_bdd/plugin/debug_mcp/entrypoint.py` | 35-28 | `35-28 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-28.md` |
| `src/pytest_bdd/plugin/debug_mcp/failure.py` | 35-28 | `35-28 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-28.md` |
| `src/pytest_bdd/plugin/debug_mcp/hook.py` | 35-28 | `35-28 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-28.md` |
| `src/pytest_bdd/plugin/debug_mcp/hookspec.py` | 35-28 | `35-28 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-28.md` |
| `src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py` | 35-29 | `35-29 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-29.md` |
| `src/pytest_bdd/plugin/debug_mcp/options.py` | 35-29 | `35-29 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-29.md` |
| `src/pytest_bdd/plugin/debug_mcp/plugin.py` | 35-29 | `35-29 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-29.md` |
| `src/pytest_bdd/plugin/debug_mcp/queue.py` | 35-29 | `35-29 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-29.md` |
| `src/pytest_bdd/plugin/debug_mcp/schemas.py` | 35-29 | `35-29 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-29.md` |
| `src/pytest_bdd/plugin/debug_mcp/sidecar.py` | 35-30 | `35-30 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-30.md` |
| `src/pytest_bdd/plugin/debug_mcp/state.py` | 35-30 | `35-30 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-30.md` |
| `src/pytest_bdd/plugin/debug_mcp/xdist.py` | 35-30 | `35-30 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-30.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py` | 35-30 | `35-30 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-30.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` | 35-30 | `35-30 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-30.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` | 35-31 | `35-31 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-31.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py` | 35-31 | `35-31 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-31.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/html_report.py` | 35-31 | `35-31 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-31.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py` | 35-31 | `35-31 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-31.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/__init__.py` | 35-31 | `35-31 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-31.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/ci.py` | 35-32 | `35-32 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-32.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/core.py` | 35-32 | `35-32 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-32.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/hooks.py` | 35-32 | `35-32 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-32.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py` | 35-32 | `35-32 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-32.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py` | 35-32 | `35-32 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-32.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py` | 35-33 | `35-33 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-33.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py` | 35-33 | `35-33 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-33.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` | 35-33 | `35-33 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-33.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py` | 35-33 | `35-33 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-33.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` | 35-33 | `35-33 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-33.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/resources/__init__.py` | 35-34 | `35-34 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-34.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/__init__.py` | 35-34 | `35-34 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-34.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/__init__.py` | 35-34 | `35-34 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-34.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py` | 35-34 | `35-34 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-34.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py` | 35-34 | `35-34 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-34.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/runtime_support.py` | 35-35 | `35-35 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-35.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py` | 35-35 | `35-35 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-35.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py` | 35-35 | `35-35 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-35.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/session.py` | 35-35 | `35-35 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-35.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py` | 35-35 | `35-35 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-35.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/__init__.py` | 35-36 | `35-36 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-36.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/core.py` | 35-36 | `35-36 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-36.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/static_helpers.py` | 35-36 | `35-36 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-36.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/stream_relay.py` | 35-36 | `35-36 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-36.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py` | 35-36 | `35-36 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-36.md` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/xdist_worker.py` | 35-37 | `35-37 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-37.md` |
| `src/pytest_bdd/plugin/gherkin_terminal_reporter/entrypoint.py` | 35-37 | `35-37 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-37.md` |
| `src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py` | 35-37 | `35-37 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-37.md` |
| `src/pytest_bdd/plugin/gherkin_terminal_reporter/hook.py` | 35-37 | `35-37 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-37.md` |
| `src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py` | 35-37 | `35-37 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-37.md` |
| `src/pytest_bdd/plugin/pickle_runner/__init__.py` | 35-38 | `35-38 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-38.md` |
| `src/pytest_bdd/plugin/pickle_runner/api_compatibility.py` | 35-38 | `35-38 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-38.md` |
| `src/pytest_bdd/plugin/pickle_runner/const.py` | 35-38 | `35-38 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-38.md` |
| `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` | 35-38 | `35-38 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-38.md` |
| `src/pytest_bdd/plugin/pickle_runner/hook.py` | 35-38 | `35-38 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-38.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin.py` | 35-39 | `35-39 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-39.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/__init__.py` | 35-39 | `35-39 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-39.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/executor.py` | 35-39 | `35-39 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-39.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/pickle_runner/plugin/runner_plugin.py` | 35-39 | `35-39 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-39.md` |
| `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` | 35-39 | `35-39 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-39.md` |
| `src/pytest_bdd/plugin/pickle_runner/status_policy.py` | 35-40 | `35-40 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-40.md` |
| `src/pytest_bdd/plugin/scenario_reporter/entrypoint.py` | 35-40 | `35-40 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-40.md` |
| `src/pytest_bdd/plugin/scenario_reporter/hook.py` | 35-40 | `35-40 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-40.md` |
| `src/pytest_bdd/plugin/scenario_reporter/plugin.py` | 35-40 | `35-40 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-40.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/_helpers.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` | 35-40 | `35-40 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-40.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/helpers.py` | 35-41 | `35-41 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-41.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/hook.py` | 35-41 | `35-41 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-41.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` | 35-41 | `35-41 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-41.md` |
| `src/pytest_bdd/plugin/scenario_test_collector/unbound.py` | 35-41 | `35-41 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-41.md` |
| `src/pytest_bdd/plugin/struct_bdd/entrypoint.py` | 35-41 | `35-41 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-41.md` |
| `src/pytest_bdd/plugin/struct_bdd/hook.py` | 35-42 | `35-42 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-42.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/__init__.py` | 35-42 | `35-42 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-42.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/_base.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/_steps.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/base.py` | 35-42 | `35-42 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-42.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/plugin/struct_bdd/model/steps.py` | 35-42 | `35-42 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-42.md` |
| `src/pytest_bdd/plugin/struct_bdd/model_builder.py` | 35-42 | `35-42 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-42.md` |
| `src/pytest_bdd/plugin/struct_bdd/parser.py` | 35-43 | `35-43 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-43.md` |
| `src/pytest_bdd/plugin/struct_bdd/plugin.py` | 35-43 | `35-43 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-43.md` |
| `src/pytest_bdd/plugin/test_group_ordering/entrypoint.py` | 35-43 | `35-43 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-43.md` |
| `src/pytest_bdd/plugin/test_group_ordering/hook.py` | 35-43 | `35-43 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-43.md` |
| `src/pytest_bdd/plugin/test_group_ordering/plugin.py` | 35-43 | `35-43 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-43.md` |
| `src/pytest_bdd/scenario.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/scenario_locator.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/scenario_locator/__init__.py` | 35-44 | `35-44 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-44.md` |
| `src/pytest_bdd/scenario_locator/base.py` | 35-44 | `35-44 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-44.md` |
| `src/pytest_bdd/scenario_locator/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/scenario_locator/file_locator.py` | 35-44 | `35-44 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-44.md` |
| `src/pytest_bdd/scenario_locator/url_locator.py` | 35-44 | `35-44 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-44.md` |
| `src/pytest_bdd/script/__init__.py` | 35-44 | `35-44 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-44.md` |
| `src/pytest_bdd/script/_feature_tree.py` | 35-45 | `35-45 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-45.md` |
| `src/pytest_bdd/script/bdd_tree_to_rst.py` | 35-45 | `35-45 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-45.md` |
| `src/pytest_bdd/script/compatibility_matrix.py` | 35-45 | `35-45 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-45.md` |
| `src/pytest_bdd/script/message_capability_governance/__init__.py` | 35-45 | `35-45 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-45.md` |
| `src/pytest_bdd/script/message_capability_governance/__main__.py` | 35-45 | `35-45 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-45.md` |
| `src/pytest_bdd/script/message_capability_governance/capabilities.py` | 35-46 | `35-46 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-46.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/__init__.py` | 35-46 | `35-46 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-46.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/_argparse.py` | 35-46 | `35-46 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-46.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/_core.py` | 35-46 | `35-46 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-46.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/_report.py` | 35-46 | `35-46 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-46.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/_utils.py` | 35-47 | `35-47 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-47.md` |
| `src/pytest_bdd/script/message_capability_governance/cli/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/script/message_capability_governance/decisions.py` | 35-47 | `35-47 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-47.md` |
| `src/pytest_bdd/script/message_capability_governance/schema.py` | 35-47 | `35-47 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-47.md` |
| `src/pytest_bdd/script/render_cucumber_formatters.py` | 35-47 | `35-47 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-47.md` |
| `src/pytest_bdd/script/sync_messages_contract_schemas.py` | 35-47 | `35-47 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-47.md` |
| `src/pytest_bdd/script/validate_feature_headings.py` | 35-48 | `35-48 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-48.md` |
| `src/pytest_bdd/steps/__init__.py` | 35-48 | `35-48 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-48.md` |
| `src/pytest_bdd/steps/decorators.py` | 35-48 | `35-48 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-48.md` |
| `src/pytest_bdd/steps/definition.py` | 35-48 | `35-48 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-48.md` |
| `src/pytest_bdd/steps/manager.py` | 35-48 | `35-48 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-48.md` |
| `src/pytest_bdd/steps/matcher.py` | 35-49 | `35-49 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-49.md` |
| `src/pytest_bdd/steps/registry.py` | 35-49 | `35-49 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-49.md` |
| `src/pytest_bdd/tag_expression.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/template/__init__.py` | 35-49 | `35-49 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-49.md` |
| `src/pytest_bdd/testing/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/testing/cck.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/types/__init__.py` | 35-49 | `35-49 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-49.md` |
| `src/pytest_bdd/types/exception.py` | 35-49 | `35-49 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-49.md` |
| `src/pytest_bdd/types/failure_reasons.py` | 35-50 | `35-50 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-50.md` |
| `src/pytest_bdd/types/json.py` | 35-50 | `35-50 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-50.md` |
| `src/pytest_bdd/types/protocol.py` | 35-50 | `35-50 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-50.md` |
| `src/pytest_bdd/types/warning.py` | 35-50 | `35-50 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-50.md` |
| `src/pytest_bdd/util/cucumber_formatter_support/__init__.py` | 35-50 | `35-50 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-50.md` |
| `src/pytest_bdd/util/cucumber_formatter_support/base.py` | 35-51 | `35-51 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-51.md` |
| `src/pytest_bdd/util/cucumber_formatter_support/registry.py` | 35-51 | `35-51 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-51.md` |
| `src/pytest_bdd/util/cucumber_formatter_support/standalone.py` | 35-51 | `35-51 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-51.md` |
| `src/pytest_bdd/util/cucumber_formatters.py` | 35-51 | `35-51 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-51.md` |
| `src/pytest_bdd/util/data_table.py` | 35-51 | `35-51 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-51.md` |
| `src/pytest_bdd/util/inspect_extra.py` | 35-52 | `35-52 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-52.md` |
| `src/pytest_bdd/util/live_reporting.py` | 35-52 | `35-52 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-52.md` |
| `src/pytest_bdd/util/matrix.py` | 35-52 | `35-52 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-52.md` |
| `src/pytest_bdd/util/npm_resource.py` | 35-52 | `35-52 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-52.md` |
| `src/pytest_bdd/util/other.py` | 35-52 | `35-52 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-52.md` |
| `src/pytest_bdd/util/packaging.py` | 35-53 | `35-53 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-53.md` |
| `src/pytest_bdd/util/pytest_extra.py` | 35-53 | `35-53 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-53.md` |
| `src/pytest_bdd/util/temp_root.py` | 35-53 | `35-53 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-53.md` |
| `src/pytest_bdd/util/tests_group_ordering.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/util/tests_group_ordering/__init__.py` | 35-53 | `35-53 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-53.md` |
| `src/pytest_bdd/util/tests_group_ordering/barrier.py` | 35-53 | `35-53 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-53.md` |
| `src/pytest_bdd/util/tests_group_ordering/config.py` | 35-54 | `35-54 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-54.md` |
| `src/pytest_bdd/util/tests_group_ordering/facade.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd/util/tests_group_ordering/marker.py` | 35-54 | `35-54 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-54.md` |
| `src/pytest_bdd/util/toolz_extra.py` | 35-54 | `35-54 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-54.md` |
| `src/pytest_bdd/util/toolz_test.py` | 35-54 | `35-54 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-54.md` |
| `src/pytest_bdd/util/url.py` | 35-54 | `35-54 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-54.md` |
| `src/pytest_bdd/util/webloc.py` | 35-55 | `35-55 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-55.md` |
| `src/pytest_bdd/util/xdist.py` | 35-55 | `35-55 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-55.md` |
| `src/pytest_bdd/utils.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd_toolchain/__init__.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd_toolchain/assertion/__init__.py` | 35-55 | `35-55 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-55.md` |
| `src/pytest_bdd_toolchain/assertion/formatter.py` | 35-55 | `35-55 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-55.md` |
| `src/pytest_bdd_toolchain/assertion/message_governance.py` | 35-55 | `35-55 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-55.md` |
| `src/pytest_bdd_toolchain/assertion/message_stream.py` | 35-56 | `35-56 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-56.md` |
| `src/pytest_bdd_toolchain/assets/__init__.py` | 35-56 | `35-56 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-56.md` |
| `src/pytest_bdd_toolchain/assets/docker/__init__.py` | 35-56 | `35-56 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-56.md` |
| `src/pytest_bdd_toolchain/assets/docker/remote_xdist/__init__.py` | 35-56 | `35-56 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-56.md` |
| `src/pytest_bdd_toolchain/case/compat/__init__.py` | 35-56 | `35-56 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-56.md` |
| `src/pytest_bdd_toolchain/case/compat/test_ci_matrix_completeness.py` | 35-57 | `35-57 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-57.md` |
| `src/pytest_bdd_toolchain/case/compat/test_existing_support_regression.py` | 35-57 | `35-57 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-57.md` |
| `src/pytest_bdd_toolchain/case/compat/test_failure_messages.py` | 35-57 | `35-57 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-57.md` |
| `src/pytest_bdd_toolchain/case/compat/test_group_classification.py` | 35-57 | `35-57 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-57.md` |
| `src/pytest_bdd_toolchain/case/compat/test_group_inventory.py` | 35-57 | `35-57 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-57.md` |
| `src/pytest_bdd_toolchain/case/compat/test_group_migration_threshold.py` | 35-58 | `35-58 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-58.md` |
| `src/pytest_bdd_toolchain/case/compat/test_group_no_duplicates.py` | 35-58 | `35-58 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-58.md` |
| `src/pytest_bdd_toolchain/case/compat/test_hook_run_api_surface.py` | 35-58 | `35-58 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-58.md` |
| `src/pytest_bdd_toolchain/case/compat/test_matrix_expansion.py` | 35-58 | `35-58 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-58.md` |
| `src/pytest_bdd_toolchain/case/compat/test_matrix_rules.py` | 35-58 | `35-58 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-58.md` |
| `src/pytest_bdd_toolchain/case/compat/test_pair_validation.py` | 35-59 | `35-59 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-59.md` |
| `src/pytest_bdd_toolchain/case/compat/test_public_api_exports.py` | 35-59 | `35-59 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-59.md` |
| `src/pytest_bdd_toolchain/case/compat/test_render_cucumber_formatters.py` | 35-59 | `35-59 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-59.md` |
| `src/pytest_bdd_toolchain/case/compat/test_tox_env_stability.py` | 35-59 | `35-59 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-59.md` |
| `src/pytest_bdd_toolchain/case/conftest.py` | 35-59 | `35-59 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-59.md` |
| `src/pytest_bdd_toolchain/case/contract/__init__.py` | 35-60 | `35-60 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-60.md` |
| `src/pytest_bdd_toolchain/case/contract/cck/__init__.py` | 35-60 | `35-60 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-60.md` |
| `src/pytest_bdd_toolchain/case/contract/cck/cck.py` | 35-60 | `35-60 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-60.md` |
| `src/pytest_bdd_toolchain/case/contract/cck/conftest.py` | 35-60 | `35-60 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-60.md` |
| `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py` | 35-60 | `35-60 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-60.md` |
| `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py` | 35-61 | `35-61 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-61.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/__init__.py` | 35-61 | `35-61 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-61.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/test_cucumber_formatter_report_doc_parse.py` | 35-61 | `35-61 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-61.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/test_development_rst.py` | 35-61 | `35-61 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-61.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/test_doc.py` | 35-61 | `35-61 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-61.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/test_docstrings.py` | 35-62 | `35-62 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-62.md` |
| `src/pytest_bdd_toolchain/case/contract/doc/test_features_repository_heading_baseline.py` | 35-62 | `35-62 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-62.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/__init__.py` | 35-62 | `35-62 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-62.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/__init__.py` | 35-62 | `35-62 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-62.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/conftest.py` | 35-62 | `35-62 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-62.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_consumption_ui.py` | 35-63 | `35-63 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-63.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_hook_vs_import_golden.py` | 35-63 | `35-63 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-63.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_plugin_hook_ingestion.py` | 35-63 | `35-63 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-63.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_plugin_ndjson_import.py` | 35-63 | `35-63 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-63.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_cli_contract.py` | 35-63 | `35-63 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-63.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_converter_contract.py` | 35-64 | `35-64 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-64.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_golden_parity.py` | 35-64 | `35-64 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-64.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_hypothesis.py` | 35-64 | `35-64 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-64.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_mapping_contract.py` | 35-64 | `35-64 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-64.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_native_parity_and_xdist.py` | 35-64 | `35-64 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-64.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_pytest_bdd_field_coverage.py` | 35-65 | `35-65 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-65.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_schema_field_coverage.py` | 35-65 | `35-65 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-65.md` |
| `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_schema_validation.py` | 35-65 | `35-65 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-65.md` |
| `src/pytest_bdd_toolchain/case/contract/generation/__init__.py` | 35-65 | `35-65 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-65.md` |
| `src/pytest_bdd_toolchain/case/contract/generation/test_template_packaging.py` | 35-65 | `35-65 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-65.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/__init__.py` | 35-66 | `35-66 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-66.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_capability_id_normalization.py` | 35-66 | `35-66 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-66.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_coverage.py` | 35-66 | `35-66 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-66.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_execution_message_adapter_roundtrip.py` | 35-66 | `35-66 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-66.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_governance.py` | 35-66 | `35-66 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-66.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_governance_cli_contract.py` | 35-67 | `35-67 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-67.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_governance_matrix_fixed.py` | 35-67 | `35-67 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-67.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_baseline_diff.py` | 35-67 | `35-67 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-67.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_capability_inventory.py` | 35-67 | `35-67 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-67.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_governance_checklist.py` | 35-67 | `35-67 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-67.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_status_governance.py` | 35-68 | `35-68 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-68.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_typing_regression.py` | 35-68 | `35-68 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-68.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_message_validation.py` | 35-68 | `35-68 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-68.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_messages.py` | 35-68 | `35-68 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-68.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_messages_feature_suite.py` | 35-68 | `35-68 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-68.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_xdist_message_consolidation.py` | 35-69 | `35-69 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-69.md` |
| `src/pytest_bdd_toolchain/case/contract/messages/test_xdist_remote_transport.py` | 35-69 | `35-69 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-69.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/__init__.py` | 35-69 | `35-69 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-69.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/conftest.py` | 35-69 | `35-69 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-69.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/probes/test_failing_step_runtime.py` | 35-69 | `35-69 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-69.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/probes/test_parse_error_runtime.py` | 35-70 | `35-70 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-70.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/probes/test_undefined_parameter_runtime.py` | 35-70 | `35-70 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-70.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/test_full_capability_governance.py` | 35-70 | `35-70 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-70.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/test_mandatory_attachments.py` | 35-70 | `35-70 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-70.md` |
| `src/pytest_bdd_toolchain/case/contract/messages_coverage/test_run_governance_regression.py` | 35-70 | `35-70 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-70.md` |
| `src/pytest_bdd_toolchain/case/contract/scripts/__init__.py` | 35-71 | `35-71 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-71.md` |
| `src/pytest_bdd_toolchain/case/contract/scripts/test_spec_prefix_resolution.py` | 35-71 | `35-71 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-71.md` |
| `src/pytest_bdd_toolchain/case/contract/scripts/test_sync_messages_contract_schemas.py` | 35-71 | `35-71 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-71.md` |
| `src/pytest_bdd_toolchain/case/contract/support/__init__.py` | 35-71 | `35-71 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-71.md` |
| `src/pytest_bdd_toolchain/case/contract/support/test_cucumber_formatters.py` | 35-71 | `35-71 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-71.md` |
| `src/pytest_bdd_toolchain/case/contract/test_act_workflows.py` | 35-72 | `35-72 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-72.md` |
| `src/pytest_bdd_toolchain/case/contract/test_compatibility_contract.py` | 35-72 | `35-72 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-72.md` |
| `src/pytest_bdd_toolchain/case/contract/test_cucumber_formatter_cli_contract.py` | 35-72 | `35-72 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-72.md` |
| `src/pytest_bdd_toolchain/case/contract/test_cucumber_json_dispatcher_contract.py` | 35-72 | `35-72 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-72.md` |
| `src/pytest_bdd_toolchain/case/contract/test_empty_heading_validation_contract.py` | 35-72 | `35-72 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-72.md` |
| `src/pytest_bdd_toolchain/case/contract/test_event_message_reporting_contract.py` | 35-73 | `35-73 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-73.md` |
| `src/pytest_bdd_toolchain/case/contract/test_feature_doc_ordering_contract.py` | 35-73 | `35-73 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-73.md` |
| `src/pytest_bdd_toolchain/case/contract/test_formatter_golden_parity.py` | 35-73 | `35-73 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-73.md` |
| `src/pytest_bdd_toolchain/case/contract/test_hook_lifecycle_non_null_contract.py` | 35-73 | `35-73 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-73.md` |
| `src/pytest_bdd_toolchain/case/contract/test_jinja2_doc_generation_contract.py` | 35-73 | `35-73 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-73.md` |
| `src/pytest_bdd_toolchain/case/contract/test_large_file_contract.py` | 35-74 | `35-74 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-74.md` |
| `src/pytest_bdd_toolchain/case/contract/test_messages_capability_coverage_contract.py` | 35-74 | `35-74 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-74.md` |
| `src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py` | 35-74 | `35-74 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-74.md` |
| `src/pytest_bdd_toolchain/case/contract/test_plugin_boundary_contract.py` | 35-74 | `35-74 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-74.md` |
| `src/pytest_bdd_toolchain/case/contract/test_plugin_patterns_contract.py` | 35-74 | `35-74 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-74.md` |
| `src/pytest_bdd_toolchain/case/contract/test_plugin_structure_contract.py` | 35-75 | `35-75 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-75.md` |
| `src/pytest_bdd_toolchain/case/contract/test_python_scripts.py` | 35-75 | `35-75 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-75.md` |
| `src/pytest_bdd_toolchain/case/contract/test_run_contract.py` | 35-75 | `35-75 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-75.md` |
| `src/pytest_bdd_toolchain/case/contract/test_standalone_rendering_boundary_contract.py` | 35-75 | `35-75 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-75.md` |
| `src/pytest_bdd_toolchain/case/contract/test_xdist_consolidated_stream_contract.py` | 35-75 | `35-75 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-75.md` |
| `src/pytest_bdd_toolchain/case/contract/test_xdist_worker_controller_boundary_contract.py` | 35-76 | `35-76 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-76.md` |
| `src/pytest_bdd_toolchain/case/e2e/__init__.py` | 35-76 | `35-76 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-76.md` |
| `src/pytest_bdd_toolchain/case/e2e/conftest.py` | 35-76 | `35-76 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-76.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/__init__.py` | 35-76 | `35-76 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-76.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_01_tutorial_01_launch.py` | 35-76 | `35-76 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-76.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_01_non_strict_gherkin.py` | 35-77 | `35-77 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-77.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_02_tag_conversion.py` | 35-77 | `35-77 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-77.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_03_markdown_parsing.py` | 35-77 | `35-77 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-77.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_04_localization.py` | 35-77 | `35-77 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-77.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_05_rule.py` | 35-77 | `35-77 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-77.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_06_tag.py` | 35-78 | `35-78 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-78.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_07_description.py` | 35-78 | `35-78 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-78.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_08_error_reporting.py` | 35-78 | `35-78 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-78.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_01_scenario_without_steps.py` | 35-78 | `35-78 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-78.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_02_scenario_search_from_base_url.py` | 35-78 | `35-78 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-78.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_03_scenario_function_loader.py` | 35-79 | `35-79 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-79.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_04_http_feature_loading.py` | 35-79 | `35-79 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-79.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_05_autoload.py` | 35-79 | `35-79 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-79.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_06_feature_base_directory_resolution.py` | 35-79 | `35-79 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-79.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_07_scenario_search_from_base_directory.py` | 35-79 | `35-79 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-79.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_02_feature_09_load_08_batch_collection.py` | 35-80 | `35-80 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-80.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_01_scenario_binding.py` | 35-80 | `35-80 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-80.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_02_tag.py` | 35-80 | `35-80 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-80.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_03_description.py` | 35-80 | `35-80 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-80.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_04_tag_filtering.py` | 35-80 | `35-80 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-80.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_05_alias.py` | 35-81 | `35-81 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-81.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_06_scenarios_loader.py` | 35-81 | `35-81 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-81.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_07_background.py` | 35-81 | `35-81 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-81.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_08_outline_01_runtime_expansion.py` | 35-81 | `35-81 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-81.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_08_outline_02_examples_tag.py` | 35-81 | `35-81 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-81.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_03_scenario_08_outline_03_empty_values.py` | 35-82 | `35-82 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-82.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_04_step_01_doc_string.py` | 35-82 | `35-82 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-82.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_04_step_02_data_table.py` | 35-82 | `35-82 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-82.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_04_step_03_step_definition_bounding.py` | 35-82 | `35-82 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-82.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_04_step_04_step_lifecycle_and_errors.py` | 35-82 | `35-82 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-82.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_01_pytest_fixtures_substitution.py` | 35-83 | `35-83 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-83.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_02_target_fixtures_specification.py` | 35-83 | `35-83 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-83.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_03_parameters_01_conversion.py` | 35-83 | `35-83 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-83.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_03_parameters_02_parsing_by_custom_parser.py` | 35-83 | `35-83 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-83.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_03_parameters_03_injection_as_fixtures.py` | 35-83 | `35-83 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-83.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_03_parameters_04_parsing.py` | 35-84 | `35-84 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-84.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_05_step_definition_03_parameters_05_defaults.py` | 35-84 | `35-84 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-84.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_06_structbdd_01_steps.py` | 35-84 | `35-84 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-84.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_06_structbdd_02_structbdd_edge_cases.py` | 35-84 | `35-84 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-84.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_01_gherkin_terminal_reporter.py` | 35-84 | `35-84 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-84.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_02_gathering.py` | 35-85 | `35-85 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-85.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_03_allure_scenario.py` | 35-85 | `35-85 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-85.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_04_allure_outline.py` | 35-85 | `35-85 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-85.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_05_cucumber_json_reporter.py` | 35-85 | `35-85 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-85.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_07_xdist_html_reporting.py` | 35-85 | `35-85 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-85.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_08_xdist_remote_network_reporting.py` | 35-86 | `35-86 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-86.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_07_report_09_cucumber_formatter_reports.py` | 35-86 | `35-86 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-86.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_08_go_parser_01_go_parser_backend.py` | 35-86 | `35-86 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-86.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_10_heading_validation_01_heading_validation.py` | 35-86 | `35-86 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-86.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_11_mimetype_01_mimetype_detection.py` | 35-86 | `35-86 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-86.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_11_mimetype_02_edge_cases.py` | 35-87 | `35-87 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-87.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters_01_junit_xml_reporter.py` | 35-87 | `35-87 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-87.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters_02_progress_formatters.py` | 35-87 | `35-87 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-87.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters_03_snippets_formatter.py` | 35-87 | `35-87 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-87.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters_04_summary_formatter.py` | 35-87 | `35-87 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-87.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_12_formatters_05_usage_statistics.py` | 35-88 | `35-88 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-88.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_13_code_generator_01_code_generation.py` | 35-88 | `35-88 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-88.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_14_scenario_reporter_01_scenario_reporting.py` | 35-88 | `35-88 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-88.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_15_compatibility_01_python_version_compatibility.py` | 35-88 | `35-88 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-88.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_16_batch_collection_01_batch_collection_edge_cases.py` | 35-88 | `35-88 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-88.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_16_batch_collection_02_edge_cases_with_large_files.py` | 35-89 | `35-89 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-89.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_17_debug_mcp_01_agentic_debugging.py` | 35-89 | `35-89 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-89.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_18_development.py` | 35-138 | `35-138 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-138.md` |
| `src/pytest_bdd_toolchain/case/e2e/feature/test_32_unbound_feature_detection_01.py` | 35-89 | `35-89 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-89.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_allure_pytest_coexistence.py` | 35-89 | `35-89 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-89.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_allure_xdist_total_report.py` | 35-90 | `35-90 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-90.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_batch_collection.py` | 35-90 | `35-90 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-90.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_cucumber_formatters.py` | 35-90 | `35-90 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-90.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_cucumber_formatters_feature.py` | 35-90 | `35-90 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-90.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_feature_065_formatters_allure.py` | 35-90 | `35-90 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-90.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_feature_066_formatters_allure_schema_field_coverage.py` | 35-91 | `35-91 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-91.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_feature_067_formatters_cck_allure_compatibility.py` | 35-91 | `35-91 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-91.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_gherkin_go_collection.py` | 35-91 | `35-91 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-91.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_messages_fixed.py` | 35-91 | `35-91 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-91.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_report_context_hierarchy.py` | 35-91 | `35-91 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-91.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_report_doc_cucumber_formatters.py` | 35-92 | `35-92 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-92.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_report_doc_gathering_html.py` | 35-92 | `35-92 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-92.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_run_lifecycle.py` | 35-92 | `35-92 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-92.md` |
| `src/pytest_bdd_toolchain/case/e2e/test_run_lifecycle_integration.py` | 35-92 | `35-92 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-92.md` |
| `src/pytest_bdd_toolchain/case/external/__init__.py` | 35-92 | `35-92 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-92.md` |
| `src/pytest_bdd_toolchain/case/external/test_docker_wsl2.py` | 35-93 | `35-93 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-93.md` |
| `src/pytest_bdd_toolchain/case/external/test_subprocess_output_attachments.py` | 35-93 | `35-93 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-93.md` |
| `src/pytest_bdd_toolchain/case/external/test_xdist_html_reporting.py` | 35-93 | `35-93 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-93.md` |
| `src/pytest_bdd_toolchain/case/external/test_xdist_message_aggregation.py` | 35-93 | `35-93 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-93.md` |
| `src/pytest_bdd_toolchain/case/external/test_xdist_remote_message_aggregation.py` | 35-93 | `35-93 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-93.md` |
| `src/pytest_bdd_toolchain/case/integration/__init__.py` | 35-94 | `35-94 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-94.md` |
| `src/pytest_bdd_toolchain/case/integration/conftest.py` | 35-94 | `35-94 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-94.md` |
| `src/pytest_bdd_toolchain/case/integration/cucumber_json/__init__.py` | 35-94 | `35-94 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-94.md` |
| `src/pytest_bdd_toolchain/case/integration/cucumber_json/test_cucumber_json_dispatcher.py` | 35-94 | `35-94 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-94.md` |
| `src/pytest_bdd_toolchain/case/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py` | 35-94 | `35-94 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-94.md` |
| `src/pytest_bdd_toolchain/case/integration/debug_mcp/test_failure_hold_lifecycle.py` | 35-95 | `35-95 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-95.md` |
| `src/pytest_bdd_toolchain/case/integration/debug_mcp/test_options_and_discovery.py` | 35-95 | `35-95 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-95.md` |
| `src/pytest_bdd_toolchain/case/integration/debug_mcp/test_sidecar_and_artifacts.py` | 35-95 | `35-95 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-95.md` |
| `src/pytest_bdd_toolchain/case/integration/debug_mcp/test_xdist_worker_discovery.py` | 35-95 | `35-95 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-95.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/__init__.py` | 35-95 | `35-95 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-95.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_batch_threshold.py` | 35-96 | `35-96 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-96.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_empty_bdd_headings_validation.py` | 35-96 | `35-96 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-96.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_foundation_cleanup.py` | 35-96 | `35-96 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-96.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_heading_validation_snippet_boundaries.py` | 35-96 | `35-96 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-96.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_mock_run.py` | 35-96 | `35-96 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-96.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_run_access_and_errors.py` | 35-97 | `35-97 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-97.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_run_hooks.py` | 35-97 | `35-97 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-97.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_same_function_name.py` | 35-97 | `35-97 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-97.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_scenario_execution_edge_cases.py` | 35-97 | `35-97 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-97.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_step_matching_ambiguous.py` | 35-97 | `35-97 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-97.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_step_matching_priority.py` | 35-98 | `35-98 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-98.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_steps.py` | 35-98 | `35-98 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-98.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_tolerant_steps.py` | 35-98 | `35-98 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-98.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_wip_steps.py` | 35-98 | `35-98 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-98.md` |
| `src/pytest_bdd_toolchain/case/integration/feature/test_xdist_parallel_integration.py` | 35-98 | `35-98 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-98.md` |
| `src/pytest_bdd_toolchain/case/integration/formatters/__init__.py` | 35-99 | `35-99 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-99.md` |
| `src/pytest_bdd_toolchain/case/integration/formatters/allure_formatter/__init__.py` | 35-99 | `35-99 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-99.md` |
| `src/pytest_bdd_toolchain/case/integration/formatters/allure_formatter/conftest.py` | 35-99 | `35-99 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-99.md` |
| `src/pytest_bdd_toolchain/case/integration/formatters/allure_formatter/test_plugin.py` | 35-99 | `35-99 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-99.md` |
| `src/pytest_bdd_toolchain/case/integration/formatters/allure_formatter/test_realtime_interception.py` | 35-99 | `35-99 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-99.md` |
| `src/pytest_bdd_toolchain/case/integration/generation/__init__.py` | 35-100 | `35-100 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-100.md` |
| `src/pytest_bdd_toolchain/case/integration/generation/test_bind_feature.py` | 35-100 | `35-100 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-100.md` |
| `src/pytest_bdd_toolchain/case/integration/generation/test_generate_missing.py` | 35-100 | `35-100 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-100.md` |
| `src/pytest_bdd_toolchain/case/integration/generation/test_generate_missing_steps.py` | 35-100 | `35-100 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-100.md` |
| `src/pytest_bdd_toolchain/case/integration/gherkin_integration/__init__.py` | 35-100 | `35-100 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-100.md` |
| `src/pytest_bdd_toolchain/case/integration/gherkin_integration/test_pickles_load.py` | 35-101 | `35-101 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-101.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/__init__.py` | 35-101 | `35-101 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-101.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_gherkin_message_reporter_pytest90_regression.py` | 35-101 | `35-101 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-101.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_gherkin_reporter_context_lifecycle.py` | 35-101 | `35-101 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-101.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_heading_validation_diagnostics.py` | 35-101 | `35-101 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-101.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_hook.py` | 35-102 | `35-102 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-102.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_hook_run_regression.py` | 35-102 | `35-102 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-102.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_live_formatter_output_relay.py` | 35-102 | `35-102 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-102.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_live_formatter_runner.py` | 35-102 | `35-102 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-102.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_live_formatter_terminal_layout.py` | 35-102 | `35-102 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-102.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_parse_error_sink.py` | 35-103 | `35-103 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-103.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_reporting_context_snapshot_unit.py` | 35-103 | `35-103 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-103.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_run_diagnostics.py` | 35-103 | `35-103 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-103.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_run_fixture_stash.py` | 35-103 | `35-103 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-103.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_run_scenario_runtime_unit.py` | 35-103 | `35-103 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-103.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_run_transitions.py` | 35-104 | `35-104 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-104.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_scenario_collection_read_hooks.py` | 35-104 | `35-104 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-104.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_scenario_locator_pipeline.py` | 35-104 | `35-104 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-104.md` |
| `src/pytest_bdd_toolchain/case/integration/hook/test_scenario_reference_resolution.py` | 35-104 | `35-104 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-104.md` |
| `src/pytest_bdd_toolchain/case/integration/library/__init__.py` | 35-104 | `35-104 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-104.md` |
| `src/pytest_bdd_toolchain/case/integration/library/test_parent.py` | 35-105 | `35-105 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-105.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/__init__.py` | 35-105 | `35-105 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-105.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_execution_message_adapter.py` | 35-105 | `35-105 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-105.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_ide_binding_contract.py` | 35-105 | `35-105 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-105.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_ide_binding_diagnostics.py` | 35-105 | `35-105 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-105.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_ide_step_bindings.py` | 35-106 | `35-106 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-106.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_message_attachments.py` | 35-106 | `35-106 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-106.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_message_emission_points.py` | 35-106 | `35-106 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-106.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_message_extension.py` | 35-106 | `35-106 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-106.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_message_outcome_mapping.py` | 35-106 | `35-106 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-106.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_startup_imports.py` | 35-107 | `35-107 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-107.md` |
| `src/pytest_bdd_toolchain/case/integration/messages/test_tolerant_step_reporting.py` | 35-107 | `35-107 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-107.md` |
| `src/pytest_bdd_toolchain/case/integration/struct_bdd/__init__.py` | 35-107 | `35-107 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-107.md` |
| `src/pytest_bdd_toolchain/case/integration/struct_bdd/test_deserialization.py` | 35-107 | `35-107 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-107.md` |
| `src/pytest_bdd_toolchain/case/integration/struct_bdd/test_gherkin_document_model_compat.py` | 35-107 | `35-107 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-107.md` |
| `src/pytest_bdd_toolchain/case/integration/struct_bdd/test_steps.py` | 35-108 | `35-108 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-108.md` |
| `src/pytest_bdd_toolchain/case/integration/test_hooks.py` | 35-108 | `35-108 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-108.md` |
| `src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` | 35-108 | `35-108 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-108.md` |
| `src/pytest_bdd_toolchain/case/integration/test_unbound_features.py` | 35-108 | `35-108 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-108.md` |
| `src/pytest_bdd_toolchain/case/perf/__init__.py` | 35-108 | `35-108 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-108.md` |
| `src/pytest_bdd_toolchain/case/perf/feature/__init__.py` | 35-109 | `35-109 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-109.md` |
| `src/pytest_bdd_toolchain/case/perf/feature/test_e2e_benchmark.py` | 35-109 | `35-109 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-109.md` |
| `src/pytest_bdd_toolchain/case/unit/__init__.py` | 35-109 | `35-109 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-109.md` |
| `src/pytest_bdd_toolchain/case/unit/args/__init__.py` | 35-109 | `35-109 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-109.md` |
| `src/pytest_bdd_toolchain/case/unit/args/cfparse/__init__.py` | 35-109 | `35-109 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-109.md` |
| `src/pytest_bdd_toolchain/case/unit/args/cfparse/test_args.py` | 35-110 | `35-110 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-110.md` |
| `src/pytest_bdd_toolchain/case/unit/args/cucumber_expression/__init__.py` | 35-110 | `35-110 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-110.md` |
| `src/pytest_bdd_toolchain/case/unit/args/cucumber_expression/test_args.py` | 35-110 | `35-110 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-110.md` |
| `src/pytest_bdd_toolchain/case/unit/args/heuristic/__init__.py` | 35-110 | `35-110 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-110.md` |
| `src/pytest_bdd_toolchain/case/unit/args/heuristic/test_args.py` | 35-110 | `35-110 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-110.md` |
| `src/pytest_bdd_toolchain/case/unit/args/parse_/__init__.py` | 35-111 | `35-111 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-111.md` |
| `src/pytest_bdd_toolchain/case/unit/args/parse_/test_args.py` | 35-111 | `35-111 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-111.md` |
| `src/pytest_bdd_toolchain/case/unit/args/regex/__init__.py` | 35-111 | `35-111 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-111.md` |
| `src/pytest_bdd_toolchain/case/unit/args/regex/test_args.py` | 35-111 | `35-111 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-111.md` |
| `src/pytest_bdd_toolchain/case/unit/args/test_arg_fixture_mix.py` | 35-111 | `35-111 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-111.md` |
| `src/pytest_bdd_toolchain/case/unit/conftest.py` | 35-112 | `35-112 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-112.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/__init__.py` | 35-112 | `35-112 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-112.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/__init__.py` | 35-112 | `35-112 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-112.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/conftest.py` | 35-112 | `35-112 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-112.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_api_hooks.py` | 35-112 | `35-112 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-112.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_collector.py` | 35-113 | `35-113 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-113.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_converter.py` | 35-113 | `35-113 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-113.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_converter_e2e.py` | 35-113 | `35-113 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-113.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_emitter.py` | 35-113 | `35-113 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-113.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_listener.py` | 35-113 | `35-113 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-113.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_mapper.py` | 35-114 | `35-114 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-114.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_message_adapter.py` | 35-114 | `35-114 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-114.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_native_plugin.py` | 35-114 | `35-114 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-114.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_reader.py` | 35-114 | `35-114 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-114.md` |
| `src/pytest_bdd_toolchain/case/unit/formatters/allure_formatter/test_step_tree.py` | 35-114 | `35-114 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-114.md` |
| `src/pytest_bdd_toolchain/case/unit/model/__init__.py` | 35-115 | `35-115 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-115.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_cucumber_formatter_adapter.py` | 35-115 | `35-115 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-115.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_feature_binding.py` | 35-115 | `35-115 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-115.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_run.py` | 35-115 | `35-115 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-115.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_run_access.py` | 35-115 | `35-115 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-115.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_run_refs.py` | 35-116 | `35-116 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-116.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_scenario_run.py` | 35-116 | `35-116 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-116.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_scenario_run_characterization.py` | 35-116 | `35-116 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-116.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_scenario_run_model.py` | 35-116 | `35-116 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-116.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_scenario_run_returns_contract.py` | 35-116 | `35-116 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-116.md` |
| `src/pytest_bdd_toolchain/case/unit/model/test_stash_access_maybe.py` | 35-117 | `35-117 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-117.md` |
| `src/pytest_bdd_toolchain/case/unit/parser/test_parser_result_contract.py` | 35-117 | `35-117 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-117.md` |
| `src/pytest_bdd_toolchain/case/unit/parser/test_parsers.py` | 35-117 | `35-117 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-117.md` |
| `src/pytest_bdd_toolchain/case/unit/test_collector.py` | 35-117 | `35-117 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-117.md` |
| `src/pytest_bdd_toolchain/case/unit/test_collector_batch.py` | 35-117 | `35-117 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-117.md` |
| `src/pytest_bdd_toolchain/case/unit/test_compatibility_semantics.py` | 35-118 | `35-118 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-118.md` |
| `src/pytest_bdd_toolchain/case/unit/test_context_error_state.py` | 35-118 | `35-118 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-118.md` |
| `src/pytest_bdd_toolchain/case/unit/test_dead_code.py` | 35-118 | `35-118 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-118.md` |
| `src/pytest_bdd_toolchain/case/unit/test_e2e_loader_shape.py` | 35-118 | `35-118 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-118.md` |
| `src/pytest_bdd_toolchain/case/unit/test_gherkin_go_bridge.py` | 35-118 | `35-118 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-118.md` |
| `src/pytest_bdd_toolchain/case/unit/test_gherkin_go_fallback.py` | 35-119 | `35-119 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-119.md` |
| `src/pytest_bdd_toolchain/case/unit/test_gherkin_go_parse.py` | 35-119 | `35-119 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-119.md` |
| `src/pytest_bdd_toolchain/case/unit/test_group_ordering.py` | 35-119 | `35-119 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-119.md` |
| `src/pytest_bdd_toolchain/case/unit/test_marker_audit.py` | 35-119 | `35-119 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-119.md` |
| `src/pytest_bdd_toolchain/case/unit/test_mypy_strict.py` | 35-119 | `35-119 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-119.md` |
| `src/pytest_bdd_toolchain/case/unit/test_no_commented_code.py` | 35-120 | `35-120 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-120.md` |
| `src/pytest_bdd_toolchain/case/unit/test_parser.py` | 35-120 | `35-120 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-120.md` |
| `src/pytest_bdd_toolchain/case/unit/test_parsers_unit.py` | 35-120 | `35-120 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-120.md` |
| `src/pytest_bdd_toolchain/case/unit/test_performance_batch.py` | 35-120 | `35-120 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-120.md` |
| `src/pytest_bdd_toolchain/case/unit/test_phase14_gap_modules.py` | 35-120 | `35-120 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-120.md` |
| `src/pytest_bdd_toolchain/case/unit/test_phase14_import_coverage.py` | 35-121 | `35-121 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-121.md` |
| `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py` | 35-121 | `35-121 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-121.md` |
| `src/pytest_bdd_toolchain/case/unit/test_scenario.py` | 35-121 | `35-121 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-121.md` |
| `src/pytest_bdd_toolchain/case/unit/test_scenario_locator.py` | 35-121 | `35-121 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-121.md` |
| `src/pytest_bdd_toolchain/case/unit/test_step_internals.py` | 35-121 | `35-121 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-121.md` |
| `src/pytest_bdd_toolchain/case/unit/test_step_policy_decorators.py` | 35-122 | `35-122 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-122.md` |
| `src/pytest_bdd_toolchain/case/unit/test_steps.py` | 35-122 | `35-122 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-122.md` |
| `src/pytest_bdd_toolchain/case/unit/test_steps_given.py` | 35-122 | `35-122 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-122.md` |
| `src/pytest_bdd_toolchain/case/unit/test_steps_unicode.py` | 35-122 | `35-122 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-122.md` |
| `src/pytest_bdd_toolchain/case/unit/test_stubs.py` | 35-122 | `35-122 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-122.md` |
| `src/pytest_bdd_toolchain/case/unit/test_tag_expression.py` | 35-123 | `35-123 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-123.md` |
| `src/pytest_bdd_toolchain/case/unit/test_tag_expression_semantics.py` | 35-123 | `35-123 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-123.md` |
| `src/pytest_bdd_toolchain/case/unit/test_test_suite_classification.py` | 35-123 | `35-123 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-123.md` |
| `src/pytest_bdd_toolchain/case/unit/test_threshold_finder.py` | 35-123 | `35-123 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-123.md` |
| `src/pytest_bdd_toolchain/case/unit/test_unbound_features.py` | 35-123 | `35-123 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-123.md` |
| `src/pytest_bdd_toolchain/case/unit/test_utils.py` | 35-124 | `35-124 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-124.md` |
| `src/pytest_bdd_toolchain/docker.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd_toolchain/docker_cluster.py` | 35-140 | `35-140 full mypy` | clean | plan 140 aggregation verification | `35-TYPING-EVIDENCE/35-140.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/__init__.py` | 35-124 | `35-124 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-124.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/__init__.py` | 35-124 | `35-124 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-124.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/file_size_rules.py` | 35-124 | `35-124 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-124.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/layer_rules.py` | 35-124 | `35-124 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-124.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/module_api_rules.py` | 35-125 | `35-125 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-125.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/noqa_rules.py` | 35-125 | `35-125 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-125.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/plugin_patterns.py` | 35-125 | `35-125 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-125.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/quality_gates.py` | 35-125 | `35-125 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-125.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/responsibility_docs.py` | 35-125 | `35-125 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-125.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/test_import_rules.py` | 35-126 | `35-126 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-126.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/test_responsibility_docs.py` | 35-126 | `35-126 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-126.md` |
| `src/pytest_bdd_toolchain/pylint_plugin/checkers/typing_rules.py` | 35-126 | `35-126 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-126.md` |
| `src/pytest_bdd_toolchain/resource/allure_reporting/outline/conftest.py` | 35-126 | `35-126 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-126.md` |
| `src/pytest_bdd_toolchain/resource/allure_reporting/outline/test_sample.py` | 35-126 | `35-126 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-126.md` |
| `src/pytest_bdd_toolchain/resource/allure_reporting/simple_scenario/conftest.py` | 35-127 | `35-127 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-127.md` |
| `src/pytest_bdd_toolchain/resource/allure_reporting/simple_scenario/test_sample.py` | 35-127 | `35-127 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-127.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/__init__.py` | 35-127 | `35-127 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-127.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/controller_entrypoint.py` | 35-127 | `35-127 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-127.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/project/__init__.py` | 35-127 | `35-127 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-127.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/project/conftest.py` | 35-128 | `35-128 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-128.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/project/remote_aggregation_case.py` | 35-128 | `35-128 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-128.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/verify_report.py` | 35-128 | `35-128 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-128.md` |
| `src/pytest_bdd_toolchain/resource/docker/remote_xdist/worker_entrypoint.py` | 35-128 | `35-128 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-128.md` |
| `src/pytest_bdd_toolchain/step/__init__.py` | 35-128 | `35-128 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-128.md` |
| `src/pytest_bdd_toolchain/step/batch_collection.py` | 35-129 | `35-129 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-129.md` |
| `src/pytest_bdd_toolchain/step/code_generator.py` | 35-129 | `35-129 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-129.md` |
| `src/pytest_bdd_toolchain/step/compatibility.py` | 35-129 | `35-129 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-129.md` |
| `src/pytest_bdd_toolchain/step/debug_mcp.py` | 35-129 | `35-129 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-129.md` |
| `src/pytest_bdd_toolchain/step/development.py` | 35-138 | `35-138 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-138.md` |
| `src/pytest_bdd_toolchain/step/formatters.py` | 35-130 | `35-130 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-130.md` |
| `src/pytest_bdd_toolchain/step/go_parser.py` | 35-130 | `35-130 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-130.md` |
| `src/pytest_bdd_toolchain/step/harness.py` | 35-130 | `35-130 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-130.md` |
| `src/pytest_bdd_toolchain/step/heading_validation.py` | 35-130 | `35-130 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-130.md` |
| `src/pytest_bdd_toolchain/step/mimetype.py` | 35-130 | `35-130 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-130.md` |
| `src/pytest_bdd_toolchain/step/scenario_reporter.py` | 35-131 | `35-131 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-131.md` |
| `src/pytest_bdd_toolchain/step/steps_allure_formatter.py` | 35-131 | `35-131 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-131.md` |
| `src/pytest_bdd_toolchain/step/steps_cck_allure.py` | 35-131 | `35-131 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-131.md` |
| `src/pytest_bdd_toolchain/step/struct_bdd.py` | 35-131 | `35-131 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-131.md` |
| `src/pytest_bdd_toolchain/step/tag_expressions.py` | 35-131 | `35-131 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-131.md` |
| `src/pytest_bdd_toolchain/tool/__init__.py` | 35-132 | `35-132 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-132.md` |
| `src/pytest_bdd_toolchain/tool/agent_orchestrator.py` | 35-132 | `35-132 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-132.md` |
| `src/pytest_bdd_toolchain/tool/analyze_responsibility_zones.py` | 35-132 | `35-132 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-132.md` |
| `src/pytest_bdd_toolchain/tool/arch.py` | 35-132 | `35-132 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-132.md` |
| `src/pytest_bdd_toolchain/tool/collect_arch_scores.py` | 35-132 | `35-132 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-132.md` |
| `src/pytest_bdd_toolchain/tool/collect_test_scores.py` | 35-133 | `35-133 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-133.md` |
| `src/pytest_bdd_toolchain/tool/cucumber_formatter/__init__.py` | 35-133 | `35-133 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-133.md` |
| `src/pytest_bdd_toolchain/tool/cucumber_formatter/registry.py` | 35-133 | `35-133 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-133.md` |
| `src/pytest_bdd_toolchain/tool/cucumber_formatter/rendering.py` | 35-133 | `35-133 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-133.md` |
| `src/pytest_bdd_toolchain/tool/cucumber_formatter/support.py` | 35-133 | `35-133 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-133.md` |
| `src/pytest_bdd_toolchain/tool/docker/__init__.py` | 35-134 | `35-134 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-134.md` |
| `src/pytest_bdd_toolchain/tool/docker/cluster.py` | 35-134 | `35-134 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-134.md` |
| `src/pytest_bdd_toolchain/tool/docker/docker.py` | 35-134 | `35-134 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-134.md` |
| `src/pytest_bdd_toolchain/tool/docker/support.py` | 35-134 | `35-134 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-134.md` |
| `src/pytest_bdd_toolchain/tool/e2e_filter.py` | 35-134 | `35-134 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-134.md` |
| `src/pytest_bdd_toolchain/tool/fill_arch_scores.py` | 35-135 | `35-135 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-135.md` |
| `src/pytest_bdd_toolchain/tool/fill_test_docstrings.py` | 35-135 | `35-135 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-135.md` |
| `src/pytest_bdd_toolchain/tool/fix_incomplete_scores.py` | 35-135 | `35-135 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-135.md` |
| `src/pytest_bdd_toolchain/tool/fix_long_lines.py` | 35-135 | `35-135 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-135.md` |
| `src/pytest_bdd_toolchain/tool/inject_responsibility_docstrings.py` | 35-135 | `35-135 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-135.md` |
| `src/pytest_bdd_toolchain/tool/inject_test_docstrings.py` | 35-136 | `35-136 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-136.md` |
| `src/pytest_bdd_toolchain/tool/message/__init__.py` | 35-136 | `35-136 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-136.md` |
| `src/pytest_bdd_toolchain/tool/message/capability_fixtures.py` | 35-136 | `35-136 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-136.md` |
| `src/pytest_bdd_toolchain/tool/message/model_coverage.py` | 35-136 | `35-136 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-136.md` |
| `src/pytest_bdd_toolchain/tool/message/stream_assertions.py` | 35-136 | `35-136 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-136.md` |
| `src/pytest_bdd_toolchain/tool/pytest_results.py` | 35-137 | `35-137 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-137.md` |
| `src/pytest_bdd_toolchain/tool/run_messages_coverage_audit.py` | 35-137 | `35-137 focused mypy` | clean | pending strict remediation | `35-TYPING-EVIDENCE/35-137.md` |



## FINAL: complete

**Modules:** 738

**Git-tracked:** 2

**Plan 140 reconciled:** all modules clean, one-owner with isolated evidence. D-02A test-suite override (pytest_bdd_toolchain.case.*) preserved.
