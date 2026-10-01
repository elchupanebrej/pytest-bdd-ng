# Graph Report - pytest-bdd-ng  (2026-10-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2597 nodes · 5688 edges · 228 communities (131 shown, 97 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 750 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Definition
- test_message_plugin.py
- test_deserialization.py
- tests/test_utils.py
- pytest_bdd/plugin.py
- StepType
- flip
- StrEnum
- Tag
- tag_expression.py
- Step
- Graphify Query 242
- pytest.py
- feature/test_steps.py
- hookspec
- StepRunner
- bdd_tree_to_rst.py
- typing.py
- test_matchers.py
- compare_distribution_version
- allure_logging.py
- ScenarioRun
- SimpleStash
- Config
- pytest_configure
- exceptions.py
- allure.py
- model.py
- Item
- Sphinx document aggregate
- StashAccess
- message_converter.py
- _fixture
- cucumber_json.py
- parse
- assert_outcomes
- model/__init__.py
- test_hook_specifications_exist
- test_matrix.py
- allure_/conftest.py
- pytest_bdd/webloc.py
- test_terminal_reporter.py
- StructBDDParser
- check_npm
- e2e/conftest.py
- gherkin_builder.py
- .name
- StepParser
- hook.py
- base.py
- ScenarioReporterPlugin
- MessageTransport
- test_stash_access.py
- Fast local debugging and triage recipe
- Migration guide from 2.3.1 to 3.0.0
- Rule: Mixing tags on feature & examples level
- test_suspect_zones.py
- scenarios
- runtime_compat.py
- library_steps.py
- scenario_report.py
- pytest_bdd/parser.py
- reporting.py
- textwrap
- test_layer_architecture.py
- message_plugin.py
- Feature documentation index
- Step parameter parsing strategies
- StepReport
- run_access.py
- workspace-describe.json
- const.py
- generate_code
- test_generate_missing.py
- feature/test_cucumber_json.py
- test_report.py
- test_parent.py
- struct_bdd/test_steps.py
- test_doc.py
- ScenarioRunner
- test_gherkin_terminal_reporter.py
- inject_fixture
- test_message_capability.py
- Feature tags and pytest test selection specification
- Step definition parameter parsing
- StructBDDPlugin
- cucumber_expression
- inspect_extra.py
- Step Parameter Fixture Injection
- os
- re
- test_generate.py
- EnvelopeRegistry
- cfparse/test_args.py
- cucumber_expression/test_args.py
- tests/conftest.py
- test_feature_base_dir.py
- Feature Tag Test Selection
- Step parameters injected as pytest fixtures
- HookCaller
- MessagePlugin
- url.py
- test_no_sctrict_gherkin.py
- test_rule.py
- Mimetype
- markdown_parser.js
- test_seam3_message_contract.py
- parse_/test_args.py
- regex/test_args.py
- func
- Feature descriptions
- Feature files search from base directory
- Report gathering
- Step data table access
- Feature: Descriptions
- Feature lookup from a base directory
- NDJSON messages and HTML reporting specification
- Gherkin step data tables
- suspect-zones.sh
- struct_bdd/parser.py
- test_no_scenario.py
- test_reporting.py
- Nested Rule Backgrounds
- Release-triggered Python package publishing
- Scenario localization
- Tutorial environment setup
- Gherkin language localization specification
- Tutorial project pytest smoke test specification
- Keyword
- Documentation build Python environment
- Plugin fixtures for BDD execution
- Gherkin feature autoload specification
- scenario() and scenarios() feature loading specification
- pytest_bdd_attach
- Rule:
- Cucumber JSON reporting integration
- pytest-bdd-ng
- Manual package release procedure
- Rule: Step definitions parameters parsing
- DefaultMapping
- test_outline.py
- attr
- Feature: Scenarios could be tagged
- get_payload_kind
- test_composite_tree_seam2_roundtrip_contract
- get_feature_and_scenario
- .decorator_builder
- test_message_serialization.py
- Join
- pytest_addhooks
- Feature: Gherkin steps bounding to steps definitions
- Rule: Feature autoload
- Feature: Gherkin features load by scenario and scenarios functions
- Feature: Step definitions parameters conversion
- facade.py
- pytest_bdd_convert_tag_to_marks
- FileScenarioLocator
- Feature: Step definitions parameters injection as fixtures
- [3.0.0] - 2026-08-30
- Feature:
- Q: #242 - graphify по этому вопросу и выполнить
- test_definition.py
- Feature: Feature files search is started from base directory
- Feature files search is started from base directory
- Feature: Step definition could override or setup new fixture
- Scenarios tags could be localized
- Feature: Scenarios tags could be converted via hooks
- Feature: Descriptions
- Feature: Steps could have docstrings
- Feature: Step definitions parameters could have default values
- Feature: Step definitions parameters parsing by custom parser
- Feature: Step definition could use pytest fixtures as step parameters
- Feature: Steps could have docstrings
- Feature: Simple project tests that use pytest-bdd-ng could be run via pytest
- RELEASING.md
- _build_scenario_param
- Gherkin Parser Background Support
- Alternative scenario flows and Cartesian expansion
- pytest Fixtures

## God Nodes (most connected - your core abstractions)
1. `Step` - 56 edges
2. `Scenario` - 51 edges
3. `Feature` - 50 edges
4. `MessagePlugin` - 49 edges
5. `StepType` - 44 edges
6. `Definition` - 41 edges
7. `Matcher` - 35 edges
8. `Config` - 34 edges
9. `Step` - 31 edges
10. `Tag` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Scenario` --references--> `1. Architectural Highlights`  [INFERRED]
  src/pytest_bdd/model/scenario.py → docs/migration/v2_to_v3.md
- `Rule` --references--> `Why this is out of scope`  [INFERRED]
  src/pytest_bdd/model/rule.py → .out-of-scope/nested-rule-backgrounds.md
- `Rule` --references--> `Nested Rule Backgrounds`  [INFERRED]
  src/pytest_bdd/model/rule.py → .out-of-scope/nested-rule-backgrounds.md
- `scenarios()` --references--> `Scenario Discovery & Execution`  [INFERRED]
  src/pytest_bdd/scenario.py → docs/migration/v2_to_v3.md
- `Feature` --uses--> `test_feature_rel_filename_from_uri_and_filename()`  [INFERRED]
  src/pytest_bdd/model/feature.py → tests/unit/model/test_feature.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Supported Gherkin background scope** — _out_of_scope_nested_rule_backgrounds_feature, _out_of_scope_nested_rule_backgrounds_gherkin_rule, _out_of_scope_nested_rule_backgrounds_feature_background, _out_of_scope_nested_rule_backgrounds_top_level_rule_background [EXTRACTED 1.00]
- **Advanced scenario execution extension surface** — documentation_pytest_bdd_hooks, documentation_plugin_fixtures, documentation_steps_left_injection [EXTRACTED 1.00]
- **CI validation tiers** — _github_workflows_main_fast_pull_request_gate, _github_workflows_main_platform_test_matrix, _github_workflows_main_end_to_end_job [EXTRACTED 1.00]
- **3.0 rewrite architecture and integration boundaries** — docs_migration_v2_to_v3_eight_layer_cycle_free_dag, docs_migration_v2_to_v3_pure_l2_domain_models, docs_migration_v2_to_v3_architecture_seams_1_to_6, docs_migration_v2_to_v3_migration_cucumber_messages, docs_migration_v2_to_v3_pytest_stash_extension [EXTRACTED 1.00]
- **Quick start workflow** — readme_gherkin_feature_files, readme_python_step_definitions, readme_pytest_fixtures, readme_pytest [EXTRACTED 1.00]
- **Feature source loading and lookup modes** — features_feature_load_autoload_feature_feature_autoload, features_feature_load_scenario_function_loader_feature_scenario_loading_functions, features_feature_load_scenario_search_from_base_directory_feature_feature_base_directory, features_feature_load_scenario_search_from_base_url_feature_feature_base_url [INFERRED 0.75]
- **Gherkin tags converted to marks and used for selection** — features_feature_tag_feature_feature_tag_selection, features_feature_tag_conversion_feature_tag_conversion_hook, features_scenario_tag_feature_scenario_tag_selection, features_scenario_outline_examples_tag_feature_examples_tag_selection [INFERRED 0.75]
- **Step argument parsing, conversion, defaults, and fixture exposure** — features_step_definition_parameters_parsing_feature_step_parameter_parsers, features_step_definition_parameters_conversion_feature_step_parameter_conversion, features_step_definition_parameters_defaults_feature_step_parameter_defaults, features_step_definition_parameters_injection_as_fixtures_feature_step_parameters_as_fixtures, features_step_definition_pytest_fixtures_substitution_feature_pytest_fixture_step_parameters, features_step_definition_target_fixtures_specification_feature_target_fixtures [INFERRED 0.75]
- **Gherkin tag scopes select pytest tests** — docs_features_feature_tag_feature_feature_tag_test_selection, docs_features_scenario_tag_feature_scenario_and_rule_tag_test_selection, docs_features_scenario_outline_examples_tag_feature_examples_tag_test_selection [INFERRED 0.85]

## Communities (228 total, 97 thin omitted)

### Community 0 - "Definition"
Cohesion: 0.13
Nodes (14): not_implemented(), tolerant(), Definition, StepDefinitionManager, StepProtocol, StepRegistryProtocol, _parser_specificity(), _resolve_callable_source_location() (+6 more)

### Community 1 - "test_message_plugin.py"
Cohesion: 0.13
Nodes (13): _enabled_config(), _hook_fixture(), _run_fixture_setup(), test_check_npm_and_cucumber_packages_exits_when_dependencies_missing(), test_hook_message_registry_is_scoped_to_plugin_instance(), test_message_plugin_disabled_is_a_noop(), test_message_plugin_disabled_when_no_options(), test_message_plugin_generates_html_report_and_removes_temp_messages_file() (+5 more)

### Community 2 - "test_deserialization.py"
Cohesion: 0.10
Nodes (25): Alternative, Step, doesnt_raise(), test_data_load(), test_join_load(), test_load_actioned_step_with_alternative_text_steps(), test_load_alternative_step_with_text_steps(), test_load_nested_steps() (+17 more)

### Community 3 - "tests/test_utils.py"
Cohesion: 0.14
Nodes (20): deepattrgetter(), setdefaultattr(), test_get_attribute(), test_get_default_for_attribute(), test_get_default_for_multi_attribute(), test_get_multi_attribute(), test_get_nested_attribute(), test_get_nested_multi_attribute() (+12 more)

### Community 4 - "pytest_bdd/plugin.py"
Cohesion: 0.06
Nodes (19): Module, Module, pytest_bdd_match_step_definition_to_step(), pytest_plugin_registered(), _pytest_pycollect_makemodule(), pytest_unconfigure(), step_matcher(), convert_str_to_python_name() (+11 more)

### Community 5 - "StepType"
Cohesion: 0.06
Nodes (26): StepType, string, trace(), given(), step(), _step(), then(), when() (+18 more)

### Community 6 - "flip"
Cohesion: 0.13
Nodes (13): flip(), test_flip_many_args(), test_flip_many_args_kwargs(), test_flip_no_args(), test_flip_no_args_but_kwargs(), func(), test_flip_one_arg(), test_flip_one_arg_kwargs() (+5 more)

### Community 7 - "StrEnum"
Cohesion: 0.08
Nodes (25): StrEnum, ParsedFeature, ParserProtocol, Mimetype, register_mimetypes(), StrEnum, Suffix, CollectorFailure (+17 more)

### Community 8 - "Tag"
Cohesion: 0.14
Nodes (16): DocString, Example, Examples, DataTable, TableCell, TableRow, Tag, _build_examples() (+8 more)

### Community 9 - "tag_expression.py"
Cohesion: 0.30
Nodes (7): parse_tag_expression(), TagExpression, test_tag_expression_boolean_operators(), test_tag_expression_complex_nested(), test_tag_expression_empty_and_whitespace(), test_tag_expression_single_tag(), test_tag_expression_syntax_error()

### Community 10 - "Step"
Cohesion: 0.12
Nodes (15): Background, Feature, Rule, Scenario, Step, test_scenario_runner_init_and_context(), test_step_runner_inject_target_fixtures(), test_step_runner_missing_step_definition_raises_not_found() (+7 more)

### Community 11 - "Graphify Query 242"
Cohesion: 0.14
Nodes (20): Contract Test Group, Execution State, FileScenarioLocator, Graphify Query 242, Message Envelope Stream and NDJSON Seam, Parser Input to Feature Model Seam, ParserRegistry, Pure Object Serialization (+12 more)

### Community 12 - "pytest.py"
Cohesion: 0.05
Nodes (8): is_pytest_version_greater_or_equal(), is_set(), is_testrun_success(), test_scenario_with_empty_example_values(), test_is_pytest_version_greater_or_equal(), test_is_set(), test_is_testrun_success(), test_typing_exports()

### Community 13 - "feature/test_steps.py"
Cohesion: 0.07
Nodes (7): test_all_steps_can_provide_fixtures(), test_multiple_given(), test_steps_parameter_mapping_acceptance_for_all_parameters(), test_steps_parameter_mapping_rejection_for_all_parameters(), test_steps_with_yield(), test_unknown_first(), test_uses_correct_step_in_the_hierarchy()

### Community 14 - "hookspec"
Cohesion: 0.14
Nodes (6): pytest_bdd_convert_tag_to_marks(), pytest_bdd_get_mimetype(), pytest_bdd_get_parser(), pytest_bdd_get_step_caller(), pytest_bdd_is_collectible(), pytest_bdd_match_step_definition_to_step()

### Community 16 - "bdd_tree_to_rst.py"
Cohesion: 0.20
Nodes (3): convert(), diff_folders(), main()

### Community 17 - "typing.py"
Cohesion: 0.15
Nodes (6): pytest_bdd_before_step_call(), pytest_bdd_run_scenario(), pytest_bdd_run_step(), pytest_bdd_step_func_lookup_error(), data_table_to_dicts(), test_data_table_to_dicts()

### Community 18 - "test_matchers.py"
Cohesion: 0.15
Nodes (10): cfparse, test_cucumber_expression_parser(), test_cucumber_expression_uses_fresh_registry(), test_cucumber_regular_expression_parser(), test_heuristic_parser(), test_heuristic_skips_unbuildable_parsers_and_is_idempotent(), test_parse_and_cfparse_parser(), test_parse_cfparse_classmethod() (+2 more)

### Community 19 - "compare_distribution_version"
Cohesion: 0.19
Nodes (7): compare_distribution_version(), get_distribution_version(), parse_version(), test_at_in_scenario(), test_tags_after_background_issue_160(), test_tags_selector(), test_packaging_versions()

### Community 20 - "allure_logging.py"
Cohesion: 0.11
Nodes (8): AllurePytestBDD, patched_asdict(), test_allure_pytest_bdd_helpers(), test_allure_pytest_bdd_lifecycle_hooks(), test_lifecycle_guards_and_param_fallback_without_allure_runtime(), test_register_and_unregister_are_noops_without_allure(), test_register_returns_none_when_no_listener_is_registered(), test_report_result_serializes_pydantic_models_and_nested_attrs()

### Community 21 - "ScenarioRun"
Cohesion: 0.13
Nodes (6): ExecutionContext, ScenarioRun, StepRun, test_execution_context_and_scenario_run(), test_scenario_run_failure_and_skip_finalization(), test_step_run_lifecycle_and_status()

### Community 22 - "SimpleStash"
Cohesion: 0.16
Nodes (8): ConfigStash, ItemStash, SessionStash, SimpleStash, _StashProxy, __init__(), test_proxy_from_item_config_session_reuses_existing_stash_objects(), test_proxy_stashes()

### Community 23 - "Config"
Cohesion: 0.11
Nodes (12): Config, LogBDDCucumberJSONProtocol, cmdline_main(), generate_and_print_code(), generate_and_print_missing_code(), pytest_bdd_message(), pytest_bdd_get_mimetype(), pytest_bdd_get_parser() (+4 more)

### Community 24 - "pytest_configure"
Cohesion: 0.23
Nodes (8): pytest_configure(), pytestbdd_id_generator(), step_registry(), IdGenerator, test_builtin_fixtures(), test_pytest_configure_lifecycle(), test_pytestbdd_id_generator_without_stash_support(), _unwrap_fixture()

### Community 25 - "exceptions.py"
Cohesion: 0.12
Nodes (14): ExamplesNotValidError, FeatureConcreteParseError, FeatureExamplesNotValidError, FeatureParseError, NoScenariosFound, PytestBDDError, PytestBDDStashError, ScenarioExamplesNotValidError (+6 more)

### Community 27 - "model.py"
Cohesion: 0.11
Nodes (15): after_convert_sub_steps_to_steps(), AndStep, before_convert_to_step(), ButStep, convert_sub_tables_to_tables(), GivenStep, Locator, Node (+7 more)

### Community 28 - "Item"
Cohesion: 0.16
Nodes (3): get_metafunc_call_arg(), Item, test_message_plugin_build_source_without_readable_file()

### Community 29 - "Sphinx document aggregate"
Cohesion: 0.17
Nodes (12): Alphabetical contributor roster, Original authors Oleg Pidsadnyi and Anatoly Bubenkov, Project authorship and contributors, Planned distributed and rerun test compatibility investigations, Upstream Gherkin Markdown support proposal #64, Markdown Gherkin parser support in 2.3.0, Pending message events: parse_error and undefined_parameter_type, Planned changes list in the legacy changelog (+4 more)

### Community 30 - "StashAccess"
Cohesion: 0.14
Nodes (8): PytestBDDStashAlreadyInitializedError, PytestBDDStashLookupError, PytestBDDStashTypeMismatchError, StashAccess, StashBound, StashKey, test_stash_access_and_stash_bound_lifecycle(), test_stash_access_supports_mappings_without_get()

### Community 31 - "message_converter.py"
Cohesion: 0.06
Nodes (50): background_to_message(), data_table_to_message(), doc_string_to_message(), envelope_from_dict(), envelope_to_dict(), feature_to_envelope(), feature_to_gherkin_document(), make_duration() (+42 more)

### Community 32 - "_fixture"
Cohesion: 0.12
Nodes (9): search_results(), attach(), parameter_type_registry(), pytestbdd_step_runner(), steps_left(), _fixture(), allure_report(), context() (+1 more)

### Community 33 - "cucumber_json.py"
Cohesion: 0.07
Nodes (25): add_options(), Argument, configure(), CucumberJson, DataTableRow, DocString, Element, ElementType (+17 more)

### Community 34 - "parse"
Cohesion: 0.17
Nodes (3): parse, StringableProtocol, stringify()

### Community 35 - "assert_outcomes"
Cohesion: 0.08
Nodes (10): assert_outcomes(), test_wrongly_outlined_duplicated_parameter_scenario(), test_wrongly_outlined_missing_parameter_scenario(), test_scenario_not_found(), test_simple(), test_scenarios(), test_scenarios_none_found(), test_scenarios_none_found_inprocess() (+2 more)

### Community 36 - "model/__init__.py"
Cohesion: 0.25
Nodes (5): GherkinDocument, test_feature_rel_filename_from_uri_and_filename(), test_gherkin_document_model(), test_legacy_model_module_shims_reexport_canonical_objects(), test_seam4_execution_context_isolation()

### Community 37 - "test_hook_specifications_exist"
Cohesion: 0.15
Nodes (7): pytest_bdd_after_scenario(), pytest_bdd_after_step(), pytest_bdd_apply_tag(), pytest_bdd_before_scenario(), pytest_bdd_before_step(), pytest_bdd_step_error(), test_hook_specifications_exist()

### Community 38 - "test_matrix.py"
Cohesion: 0.13
Nodes (14): build_parametrization(), build_scenario_parametrization(), expand_example_rows(), expand_examples(), expand_parameter_matrix(), substitute_parameters(), test_build_parametrization_and_scenario_parametrization(), test_build_scenario_parametrization_merges_heterogeneous_keys() (+6 more)

### Community 39 - "allure_/conftest.py"
Cohesion: 0.13
Nodes (12): allured_testdir(), AlluredTestdir, fake_logger(), feature_definition(), has_step(), has_test_case(), item_history_id(), item_status() (+4 more)

### Community 40 - "pytest_bdd/webloc.py"
Cohesion: 0.13
Nodes (4): read(), write(), read(), write()

### Community 41 - "test_terminal_reporter.py"
Cohesion: 0.06
Nodes (24): add_options(), check_existense(), add_options(), configure(), GherkinTerminalReporter, _normalize_spans(), add_bdd_ini(), pytest_addoption() (+16 more)

### Community 42 - "StructBDDParser"
Cohesion: 0.16
Nodes (10): StructBDDParser, test_parse_json_struct_bdd_feature(), test_parse_struct_bdd_feature_with_data_tables(), test_parse_struct_bdd_file(), test_parse_toml_struct_bdd_feature(), test_parse_yaml_struct_bdd_feature(), test_parser_defaults_to_yaml_kind(), test_parser_rejects_unsupported_kind() (+2 more)

### Community 43 - "check_npm"
Cohesion: 0.31
Nodes (9): check_npm(), check_npm_package(), _check_subprocess(), wrapper(), get_npm_root(), _npm_command(), test_npm_helpers(), test_npm_helpers_find_shim_on_path() (+1 more)

### Community 44 - "e2e/conftest.py"
Cohesion: 0.19
Nodes (10): data_table_to_dicts(), compose(), check_pytest_stdout_lines(), check_pytest_test_statuses(), copy_file(), httpserver(), run_pytest(), test_feature_load_by_http_with_base_url() (+2 more)

### Community 45 - "gherkin_builder.py"
Cohesion: 0.32
Nodes (12): _build_background(), _build_examples(), build_feature_from_dict(), _build_rule(), _build_scenario(), _build_step(), _build_steps(), _build_table_row() (+4 more)

### Community 47 - "StepParser"
Cohesion: 0.09
Nodes (6): StepParser, StepParserProtocol, _build(), heuristic, test_step_parser_build_factory(), test_step_parser_protocol()

### Community 48 - "hook.py"
Cohesion: 0.36
Nodes (4): decorator_builder(), HookConjunction, HookKind, test_hook_enums_and_decorators()

### Community 49 - "base.py"
Cohesion: 0.18
Nodes (6): StepDefinitionPatternType, _load_parser_modules(), register_fallback_parser(), register_parser(), RegistryMode, cucumber_regular_expression

### Community 51 - "MessageTransport"
Cohesion: 0.22
Nodes (4): MessageFanOutEmitter, MessageTransport, test_message_transport_buffering_and_sinks(), test_message_transport_deduplicates_sinks_and_clears_buffer()

### Community 52 - "test_stash_access.py"
Cohesion: 0.24
Nodes (5): DummyBound, PlainMapping, test_proxy_get_falls_back_for_mappings_without_get(), test_stash_create_once_persists_fresh_instance(), test_stash_key_and_simple_stash()

### Community 53 - "Fast local debugging and triage recipe"
Cohesion: 0.15
Nodes (12): Dedicated end-to-end job, Fast pull-request gate, Gherkin reporting toolchain setup, Cross-platform tox test matrix, Ruff and repository hygiene hooks, CI acceptance: matrix and dedicated e2e job, Failure-first reproduction and baseline check, Fast local debugging and triage recipe (+4 more)

### Community 54 - "Migration guide from 2.3.1 to 3.0.0"
Cohesion: 0.18
Nodes (12): Native Cucumber Expressions support, Cucumber Messages v22+ compatibility, Multi-format Gherkin and Structured BDD parsers, pytest-bdd-ng 3.0.0 release, Automated architecture and toolchain quality gates, Architecture seams 1–6, Eight-layer cycle-free architecture, Cucumber Messages NDJSON and JSON reporting (+4 more)

### Community 55 - "Rule: Mixing tags on feature & examples level"
Cohesion: 0.10
Nodes (19): Background:, Background:, Example:, Example:, Example:, Example:, Example:, Example: (+11 more)

### Community 56 - "test_suspect_zones.py"
Cohesion: 0.24
Nodes (9): _is_wsl_bash(), _resolve_bash(), suspect_zones(), test_is_wsl_bash_detects_system32_launcher(), test_mapping_table(), test_output_is_deduplicated(), test_resolve_bash_prefers_real_bash(), test_resolve_bash_returns_none_when_only_wsl_stub() (+1 more)

### Community 57 - "scenarios"
Cohesion: 0.06
Nodes (24): 1. Architectural Highlights, 2. Key Changes & Migration Steps, Migration Guide: 2.3.1 to 3.0.0, Reporting & Compatibility, Scenario Discovery & Execution, Step Definitions, Tag Filtering & Hooks, FeatureFileModule (+16 more)

### Community 58 - "runtime_compat.py"
Cohesion: 0.26
Nodes (10): CompatibilityMatrixEntry, _format_pytest_version(), _format_python_version(), is_pair_compatible(), MigrationCoverageSummary, _parse_pytest_factor(), _parse_python_factor(), test_is_pair_compatible() (+2 more)

### Community 59 - "library_steps.py"
Cohesion: 0.25
Nodes (6): Book, Catalog, a_search_type_is_performed_for_search_term(), get_books_from_data_table(), only_these_books_will_be_returned(), these_books_in_the_catalog()

### Community 60 - "scenario_report.py"
Cohesion: 0.25
Nodes (4): ScenarioReport, ScenarioReportData, StepReport, StepReportData

### Community 61 - "pytest_bdd/parser.py"
Cohesion: 0.05
Nodes (33): MarkdownTokenMatcher, BaseParser, GherkinParser, LegacyGherkinParser, MarkdownParser, ParserProtocol, ParserRegistry, test_rule_scenario_pickle_merges_feature_and_rule_backgrounds() (+25 more)

### Community 62 - "reporting.py"
Cohesion: 0.21
Nodes (4): _serialize_step(), serialize_step_keyword(), serialize_step_type(), test_serialize_step_type_and_keyword_vocabulary()

### Community 64 - "textwrap"
Cohesion: 0.11
Nodes (4): test_background_basic(), test_background_check_order(), test_multiple_features_single_file(), test_item_collection_does_not_break_on_non_function_items()

### Community 65 - "test_layer_architecture.py"
Cohesion: 0.16
Nodes (5): get_layer_for_module(), load_layers_config(), test_layer_import_enforcement(), test_layers_toml_dag_properties(), test_modules_mapping_validity()

### Community 67 - "Feature documentation index"
Cohesion: 0.15
Nodes (13): Gherkin features autoload, Feature Autoload, Gherkin features load by scenario and scenarios functions, Scenario Registration Apis, Feature tag conversion, Feature Tag Conversion Hook, Feature documentation index, End To End Feature Specifications (+5 more)

### Community 68 - "Step parameter parsing strategies"
Cohesion: 0.17
Nodes (12): Step parameter conversion specification, Step parameter conversion, Default step parameter values specification, Default step parameter values, Custom step parameter parser, Custom step parameter parser specification, Cucumber Expressions, Step parameter parsing strategies specification (+4 more)

### Community 70 - "run_access.py"
Cohesion: 0.45
Nodes (10): bind_scenario_run(), get_execution_context(), get_scenario_run(), require_execution_context(), require_scenario_run(), _resolve_stash(), set_scenario_run(), test_run_access_prefers_raw_stash_and_supports_bare_objects() (+2 more)

### Community 71 - "workspace-describe.json"
Cohesion: 0.17
Nodes (11): additionalProperties, description, type, properties, clean, root, required, description (+3 more)

### Community 72 - "const.py"
Cohesion: 0.24
Nodes (5): Cli, Ini, PytestConfigParam, Steps, add_options()

### Community 73 - "generate_code"
Cohesion: 0.23
Nodes (5): generate_code(), make_python_docstring(), make_string_literal(), print_missing_code(), test_generation_helpers()

### Community 75 - "feature/test_cucumber_json.py"
Cohesion: 0.21
Nodes (4): OfType, runandparse(), test_skipped_scenario_in_cucumber_json(), test_step_trace()

### Community 76 - "test_report.py"
Cohesion: 0.21
Nodes (4): matchreport(), OfType, test_complex_types(), test_step_trace()

### Community 77 - "test_parent.py"
Cohesion: 0.17
Nodes (5): test_child(), test_local(), test_local_both_target_fixture_and_target_fixtures(), test_local_multiple_target_fixtures(), test_parent()

### Community 78 - "struct_bdd/test_steps.py"
Cohesion: 0.15
Nodes (4): test_autoload_feature_yaml(), test_default_loader(), test_examples(), test_steps()

### Community 79 - "test_doc.py"
Cohesion: 0.33
Nodes (5): _load_bdd_tree_to_rst(), test_adjust_heading_level_shifts_headers_only(), test_convert_includes_struct_bdd_files(), test_diff_folders_reports_top_level_and_nested_differences(), test_doc_generation()

### Community 81 - "test_gherkin_terminal_reporter.py"
Cohesion: 0.20
Nodes (3): test_default_output_should_be_the_same_as_regular_terminal_reporter(), test_error_message_for_missing_steps(), test_error_message_should_be_displayed()

### Community 82 - "inject_fixture"
Cohesion: 0.29
Nodes (3): build_fixture_def(), inject_fixture(), _LegacyFixtureDefFactory

### Community 83 - "test_message_capability.py"
Cohesion: 0.26
Nodes (7): capability_is_relevant(), classify_capability_relevance(), MessageCapability, EnvelopeStatus, LifecycleCorrelation, test_message_capability_classification(), test_message_extension_pattern_and_lifecycle()

### Community 84 - "Feature tags and pytest test selection specification"
Cohesion: 0.20
Nodes (9): Scenario tag conversion hook specification, Scenario tag conversion hook, Cucumber tags, Feature tags and pytest test selection specification, pytest test selection documentation, Scenario Outline Examples tags and selection specification, Scenario Outline Examples tags and selection, Scenario tags and pytest test selection specification (+1 more)

### Community 85 - "Step definition parameter parsing"
Cohesion: 0.22
Nodes (9): Step definition parameter conversion, Step Argument Conversion, Custom Step Parser, Step definitions parsed by custom parser, Cucumber Expressions, Step definition parameter parsing, parse library, parse_type library (+1 more)

### Community 86 - "StructBDDPlugin"
Cohesion: 0.22
Nodes (5): pytest_pycollect_makemodule(), StructBDDPlugin, test_struct_bdd_plugin_get_mimetype(), test_struct_bdd_plugin_get_parser(), test_struct_bdd_plugin_is_collectible()

### Community 87 - "cucumber_expression"
Cohesion: 0.21
Nodes (3): cucumber_expression, _CucumberExpression, test_parser_constructors_reject_unsupported_input()

### Community 88 - "inspect_extra.py"
Cohesion: 0.36
Nodes (7): get_args(), get_caller_module_locals(), get_caller_module_path(), get_first_source_line(), sample_func(), test_first_source_line_falls_back_to_code_object(), test_inspect_helpers()

### Community 89 - "Step Parameter Fixture Injection"
Cohesion: 0.29
Nodes (5): Step definition parameter defaults, Step Argument Defaults, Step definition parameter injection as fixtures, Step definitions use pytest fixtures as parameters, Target fixtures for step definitions

### Community 90 - "os"
Cohesion: 0.13
Nodes (10): relpath(), resolvepath(), prefer_posix_temp_root(), compose(), flip(), test_relpath(), test_resolvepath(), test_prefer_posix_temp_root_moves_mnt_tempdir() (+2 more)

### Community 92 - "test_generate.py"
Cohesion: 0.25
Nodes (3): test_generate(), test_generate_with_quotes(), test_unicode_characters()

### Community 95 - "cucumber_expression/test_args.py"
Cohesion: 0.33
Nodes (3): test_cucumber_expression(), test_cucumber_expression_complex_type(), test_cucumber_regular_expression()

### Community 97 - "test_feature_base_dir.py"
Cohesion: 0.38
Nodes (3): prepare_testdir(), test_feature_path_by_param_ok(), test_feature_path_ok()

### Community 100 - "Feature Tag Test Selection"
Cohesion: 0.40
Nodes (6): Features could be tagged, Feature Tag Test Selection, Scenario Outline examples tags, Examples Tag Test Selection, Scenario tags, Scenario And Rule Tag Test Selection

### Community 101 - "Step parameters injected as pytest fixtures"
Cohesion: 0.40
Nodes (3): Step parameters injected as pytest fixtures specification, Pytest fixtures supplied to step functions specification, Given steps setting target fixtures specification

### Community 102 - "HookCaller"
Cohesion: 0.20
Nodes (3): HookCaller, test_hook_caller_dispatch(), test_hook_caller_is_noop_without_hook_methods()

### Community 103 - "MessagePlugin"
Cohesion: 0.16
Nodes (4): MessagePlugin, find_resource(), test_find_resource(), test_message_plugin_add_options()

### Community 104 - "url.py"
Cohesion: 0.53
Nodes (4): is_local_url(), is_url_parsable(), test_is_local_url_handles_unparsable_and_bytes_input(), test_url_helpers()

### Community 108 - "Mimetype"
Cohesion: 0.35
Nodes (8): Mimetype, test_feature_load_by_http(), test_feature_load_by_http_from_desktop_file(), test_feature_load_by_http_from_url_file(), test_feature_load_by_http_from_webloc_file(), test_feature_load_by_http_with_base_url(), test_feature_load_by_http_with_base_url_from_ini(), test_struct_bdd_feature_load_by_http()

### Community 114 - "func"
Cohesion: 0.18
Nodes (8): decorator_wrapper(), decorator(), hook(), get_marks(), wrapped(), wrapped(), _itemgetter(), func()

### Community 115 - "Feature descriptions"
Cohesion: 0.50
Nodes (4): Feature descriptions, Gherkin Free Form Descriptions, Scenario descriptions, Scenario Descriptions

### Community 116 - "Feature files search from base directory"
Cohesion: 0.50
Nodes (4): Feature files search from base directory, Feature Base Directory Resolution, Feature files search from base URL, Feature Base Url Resolution

### Community 117 - "Report gathering"
Cohesion: 0.50
Nodes (4): Cucumber HTML formatter, Cucumber Message And Html Reports, Cucumber Messages, Report gathering

### Community 118 - "Step data table access"
Cohesion: 0.50
Nodes (4): Step data table access, Step Data Tables, Step doc string access, Step Doc Strings

### Community 119 - "Feature: Descriptions"
Cohesion: 0.33
Nodes (5): Feature descriptions specification, Feature: Descriptions, Scenario:, Scenario descriptions specification, Scenario descriptions

### Community 120 - "Feature lookup from a base directory"
Cohesion: 0.50
Nodes (4): Feature lookup from a base directory specification, Feature lookup from a base directory, Feature lookup from a base URL specification, Feature lookup from a base URL

### Community 121 - "NDJSON messages and HTML reporting specification"
Cohesion: 0.50
Nodes (4): Cucumber HTML formatter, Cucumber Messages, NDJSON messages and HTML reporting specification, NDJSON messages and HTML reporting

### Community 122 - "Gherkin step data tables"
Cohesion: 0.50
Nodes (4): Gherkin step data tables specification, Gherkin step data tables, Gherkin step doc strings specification, Gherkin step doc strings

### Community 123 - "suspect-zones.sh"
Cohesion: 0.83
Nodes (3): emit(), full(), suspect-zones.sh script

### Community 126 - "test_reporting.py"
Cohesion: 0.25
Nodes (7): FeatureStub, PickleStub, ScenarioStub, test_reporter_plugin_hooks_are_noops_without_active_report(), test_scenario_report_fail_appends_remaining_scenario_steps(), test_scenario_report_serializes_uri_fallback_and_pickle_steps(), test_step_report_duration_is_zero_until_finalized()

### Community 128 - "Nested Rule Backgrounds"
Cohesion: 0.20
Nodes (9): Compatibility Tests, Cucumber Gherkin Issue 126, Feature, Gherkin Rule, Gherkin Specification, Nested Rule Hierarchy, Nested Rule Backgrounds, Prior requests (+1 more)

### Community 130 - "Scenario localization"
Cohesion: 0.67
Nodes (3): Scenario localization, Gherkin Localization, Gherkin language localization reference

### Community 131 - "Tutorial environment setup"
Cohesion: 0.67
Nodes (3): Tutorial for Behave and Cucumber users, Tutorial environment setup, Tutorial Python requirements

### Community 132 - "Gherkin language localization specification"
Cohesion: 0.67
Nodes (3): Gherkin language localization specification, Gherkin language table, Gherkin language localization

### Community 133 - "Tutorial project pytest smoke test specification"
Cohesion: 0.67
Nodes (3): Tutorial project pytest smoke test specification, pytest-bdd-ng tutorial project, Tutorial project pytest smoke test

### Community 134 - "Keyword"
Cohesion: 0.27
Nodes (8): Keyword, KeywordType, SubKeyword, test_load_actioned_step_with_text_steps(), test_load_simplest_given(), test_load_simplest_step_with_text_steps(), test_step_non_containing_data_load(), test_step_prototype_non_containing_data_load()

### Community 140 - "Rule:"
Cohesion: 0.20
Nodes (9): Background:, Feature: Features could be tagged, Rule:, Scenario:, Scenario:, Scenario:, Scenario:, Scenario: (+1 more)

### Community 172 - "Rule: Step definitions parameters parsing"
Cohesion: 0.20
Nodes (9): Background:, Example: by "cfparse", Example: by "cucumber-expressions", Example: by "cucumber-regular-expressions", Example: by "parse", Example: by "regular-expressions", Example: Heuristic parser guesses a type and builds particular parser to be applied, Feature: Step definitions parameters parsing (+1 more)

### Community 174 - "test_outline.py"
Cohesion: 0.24
Nodes (4): collect_dumped_objects(), test_outline_with_escaped_pipes(), test_outlined(), test_outlined_with_other_fixtures()

### Community 175 - "attr"
Cohesion: 0.43
Nodes (3): DummyAST, DummyIdentifiable, test_runtime_protocols()

### Community 176 - "Feature: Scenarios could be tagged"
Cohesion: 0.22
Nodes (8): Background:, Feature: Scenarios could be tagged, Scenario:, Scenario:, Scenario:, Scenario:, Scenario:, Scenario:

### Community 177 - "get_payload_kind"
Cohesion: 0.53
Nodes (4): get_payload_kind(), get_payload_merge_class(), has_single_payload(), test_message_extension_payload_helpers()

### Community 178 - "test_composite_tree_seam2_roundtrip_contract"
Cohesion: 0.46
Nodes (6): as_dict(), from_dict(), from_json(), to_json(), test_composite_tree_seam2_roundtrip_contract(), test_plain_python_values_and_unknown_key_tolerance()

### Community 182 - "Join"
Cohesion: 0.13
Nodes (4): Join, Route, Table, test_nested_sub_join_load()

### Community 184 - "Feature: Gherkin steps bounding to steps definitions"
Cohesion: 0.25
Nodes (7): Background:, Feature: Gherkin steps bounding to steps definitions, Rule: Steps could be executed by liberal step keyword decorator, Scenario: Keyworded steps could be treated as liberal by pytest command line option, Scenario: Same step is used with different keywords, Scenario: Steps are executed by corresponding step keyword decorator, Scenario: Steps could be executed by aliased step keyword decorator

### Community 186 - "Rule: Feature autoload"
Cohesion: 0.29
Nodes (6): Background:, Feature: Gherkin features autoload, Rule: Feature autoload, Scenario: Feature autoload could be disabled via command line, Scenario: Feature autoload could be disabled via pytest.ini, Scenario: Feature is loaded by default

### Community 187 - "Feature: Gherkin features load by scenario and scenarios functions"
Cohesion: 0.29
Nodes (6): Background:, Feature: Gherkin features load by scenario and scenarios functions, Scenario: "scenario" function is used as decorator, Scenario: "scenario" function is used to register feature as test, Scenario: "scenarios" function is used as decorator, Scenario: "scenarios" function is used to register feature as test

### Community 188 - "Feature: Step definitions parameters conversion"
Cohesion: 0.29
Nodes (6): Background:, Feature: Step definitions parameters conversion, Rule: for anonymous groups, Scenario:, Scenario:, Scenario: for non-anonymous groups

### Community 189 - "facade.py"
Cohesion: 0.25
Nodes (3): ParserBuildValueError, StepMatch, test_step_match_and_enums()

### Community 191 - "FileScenarioLocator"
Cohesion: 0.06
Nodes (36): make_mark(), make_mark_decorator(), _build_filter(), _build_scenario_locators_from_mark(), FileScenarioLocator, ScenarioLocatorFeatureResolver, ScenarioLocatorFilterMixin, ScenarioLocatorResolver (+28 more)

### Community 192 - "Feature: Step definitions parameters injection as fixtures"
Cohesion: 0.33
Nodes (5): Feature: Step definitions parameters injection as fixtures, Scenario: Only allowed step parameters injection as fixtures, Scenario: Step parameters are injected as fixtures by default, Scenario: Step parameters injection as fixtures could be disabled, Scenario: Step parameters renaming on injection as fixtures

### Community 193 - "[3.0.0] - 2026-08-30"
Cohesion: 0.40
Nodes (4): [3.0.0] - 2026-08-30, Architecture & Clean-Room Rewrite (refs #143, #150, #151), Changelog, Features & Protocol Compatibility

### Community 194 - "Feature:"
Cohesion: 0.40
Nodes (4): Background:, Feature:, Scenario: HTML report could be produced on the feature run, Scenario: NDJson(JSONL) could be produced on the feature run

### Community 195 - "Q: #242 - graphify по этому вопросу и выполнить"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: #242 - graphify по этому вопросу и выполнить, Source Nodes

### Community 196 - "test_definition.py"
Cohesion: 0.53
Nodes (5): dummy_step(), test_definition_as_message(), test_definition_get_parameters_and_fixtures_mapped(), test_resolve_callable_source_location(), test_resolve_callable_source_location_falls_back_without_source()

### Community 197 - "Feature: Feature files search is started from base directory"
Cohesion: 0.50
Nodes (3): Background:, Feature: Feature files search is started from base directory, Scenario:

### Community 198 - "Feature files search is started from base directory"
Cohesion: 0.50
Nodes (3): Background:, Feature files search is started from base directory, Scenario:

### Community 199 - "Feature: Step definition could override or setup new fixture"
Cohesion: 0.50
Nodes (3): Feature: Step definition could override or setup new fixture, Scenario: Multiple fixtures injection, Scenario: Single fixture injection

### Community 214 - "Gherkin Parser Background Support"
Cohesion: 0.67
Nodes (3): Feature Background, Gherkin Parser Background Support, Top-level Rule Background

## Knowledge Gaps
- **186 isolated node(s):** `feature`, `Scenario:`, `Prior requests`, `Background:`, `Scenario:` (+181 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 887 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **97 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MessageTransport` connect `MessageTransport` to `typing.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `Step` connect `Step` to `Definition`, `FileScenarioLocator`, `message_plugin.py`, `model/__init__.py`, `StepType`, `test_definition.py`, `Tag`, `gherkin_builder.py`, `.name`, `test_seam3_message_contract.py`, `test_composite_tree_seam2_roundtrip_contract`, `allure_logging.py`, `ScenarioRun`, `reporting.py`, `message_converter.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `Step` (e.g. with `Scenario` and `Background`) actually correct?**
  _`Step` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `Scenario` (e.g. with `Feature` and `1. Architectural Highlights`) actually correct?**
  _`Scenario` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `Feature` (e.g. with `Background` and `GherkinDocument`) actually correct?**
  _`Feature` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `MessagePlugin` (e.g. with `Item` and `Mimetype`) actually correct?**
  _`MessagePlugin` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `StepType` (e.g. with `given()` and `step()`) actually correct?**
  _`StepType` has 27 INFERRED edges - model-reasoned connections that need verification._