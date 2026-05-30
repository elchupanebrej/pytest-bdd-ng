# Phase 12 Classification Inventory

Every collected `test_*.py` source path is mapped to a semantic `tests/cases` target before the migration.

| Old path | New path | Semantic group | Ambiguous | Reason |
|---|---|---|---|---|
| `tests/args/cfparse/test_args.py` | `tests/cases/unit/args/cfparse/test_args.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/args/cucumber_expression/test_args.py` | `tests/cases/unit/args/cucumber_expression/test_args.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/args/heuristic/test_args.py` | `tests/cases/unit/args/heuristic/test_args.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/args/parse_/test_args.py` | `tests/cases/unit/args/parse_/test_args.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/args/regex/test_args.py` | `tests/cases/unit/args/regex/test_args.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/args/test_arg_fixture_mix.py` | `tests/cases/unit/args/test_arg_fixture_mix.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/build/test_gherkin_go_build.py` | `tests/cases/compat/build/test_gherkin_go_build.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_ci_matrix_completeness.py` | `tests/cases/compat/compatibility/test_ci_matrix_completeness.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_e2e_classification.py` | `tests/cases/compat/compatibility/test_e2e_classification.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_e2e_inventory.py` | `tests/cases/compat/compatibility/test_e2e_inventory.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_e2e_migration_threshold.py` | `tests/cases/compat/compatibility/test_e2e_migration_threshold.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_e2e_no_duplicates.py` | `tests/cases/compat/compatibility/test_e2e_no_duplicates.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_existing_support_regression.py` | `tests/cases/compat/compatibility/test_existing_support_regression.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_failure_messages.py` | `tests/cases/compat/compatibility/test_failure_messages.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_hook_run_api_surface.py` | `tests/cases/compat/compatibility/test_hook_run_api_surface.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_matrix_expansion.py` | `tests/cases/compat/compatibility/test_matrix_expansion.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_matrix_rules.py` | `tests/cases/compat/compatibility/test_matrix_rules.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_pair_validation.py` | `tests/cases/compat/compatibility/test_pair_validation.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_public_api_exports.py` | `tests/cases/compat/compatibility/test_public_api_exports.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_render_cucumber_formatters.py` | `tests/cases/compat/compatibility/test_render_cucumber_formatters.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/compatibility/test_tox_env_stability.py` | `tests/cases/compat/compatibility/test_tox_env_stability.py` | `compat` | no | compatibility, matrix, public API, build, or dependency surface checks |
| `tests/contract/test_compatibility_contract.py` | `tests/cases/contract/contract/test_compatibility_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_cucumber_formatter_cli_contract.py` | `tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_empty_heading_validation_contract.py` | `tests/cases/contract/contract/test_empty_heading_validation_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_event_message_reporting_contract.py` | `tests/cases/contract/contract/test_event_message_reporting_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_feature_doc_ordering_contract.py` | `tests/cases/contract/contract/test_feature_doc_ordering_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_formatter_golden_parity.py` | `tests/cases/contract/contract/test_formatter_golden_parity.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_hook_lifecycle_non_null_contract.py` | `tests/cases/contract/contract/test_hook_lifecycle_non_null_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_jinja2_doc_generation_contract.py` | `tests/cases/contract/contract/test_jinja2_doc_generation_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_large_file_contract.py` | `tests/cases/contract/contract/test_large_file_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_messages_capability_coverage_contract.py` | `tests/cases/contract/contract/test_messages_capability_coverage_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_plugin_boundary_contract.py` | `tests/cases/contract/contract/test_plugin_boundary_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_plugin_patterns_contract.py` | `tests/cases/contract/contract/test_plugin_patterns_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_plugin_structure_contract.py` | `tests/cases/contract/contract/test_plugin_structure_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_run_contract.py` | `tests/cases/contract/contract/test_run_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_standalone_rendering_boundary_contract.py` | `tests/cases/contract/contract/test_standalone_rendering_boundary_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_xdist_consolidated_stream_contract.py` | `tests/cases/contract/contract/test_xdist_consolidated_stream_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/contract/test_xdist_worker_controller_boundary_contract.py` | `tests/cases/contract/contract/test_xdist_worker_controller_boundary_contract.py` | `contract` | no | boundary, schema, formatter, structure, or golden contract verification |
| `tests/doc/test_cucumber_formatter_report_doc_parse.py` | `tests/cases/contract/doc/test_cucumber_formatter_report_doc_parse.py` | `contract` | no | documentation and generated feature-doc contract checks |
| `tests/doc/test_development_rst.py` | `tests/cases/contract/doc/test_development_rst.py` | `contract` | no | documentation and generated feature-doc contract checks |
| `tests/doc/test_doc.py` | `tests/cases/contract/doc/test_doc.py` | `contract` | no | documentation and generated feature-doc contract checks |
| `tests/doc/test_docstrings.py` | `tests/cases/contract/doc/test_docstrings.py` | `contract` | no | documentation and generated feature-doc contract checks |
| `tests/doc/test_features_repository_heading_baseline.py` | `tests/cases/contract/doc/test_features_repository_heading_baseline.py` | `contract` | no | documentation and generated feature-doc contract checks |
| `tests/e2e/test_cucumber_formatters.py` | `tests/cases/e2e/e2e/test_cucumber_formatters.py` | `e2e` | no | full executable user workflow or feature-doc acceptance binding |
| `tests/e2e/test_cucumber_formatters_feature.py` | `tests/cases/e2e/e2e/test_cucumber_formatters_feature.py` | `e2e` | no | full executable user workflow or feature-doc acceptance binding |
| `tests/e2e/test_e2e.py` | `tests/cases/e2e/e2e/test_e2e.py` | `e2e` | no | full executable user workflow or feature-doc acceptance binding |
| `tests/e2e/test_report_doc_cucumber_formatters.py` | `tests/cases/e2e/e2e/test_report_doc_cucumber_formatters.py` | `e2e` | no | full executable user workflow or feature-doc acceptance binding |
| `tests/e2e/test_report_doc_gathering_html.py` | `tests/cases/e2e/e2e/test_report_doc_gathering_html.py` | `e2e` | no | full executable user workflow or feature-doc acceptance binding |
| `tests/e2e/test_subprocess_output_attachments.py` | `tests/cases/external/e2e/test_subprocess_output_attachments.py` | `external` | no | external, subprocess, xdist, Docker, or platform harness workflow |
| `tests/e2e/test_xdist_html_reporting.py` | `tests/cases/external/e2e/test_xdist_html_reporting.py` | `external` | no | external, subprocess, xdist, Docker, or platform harness workflow |
| `tests/e2e/test_xdist_message_aggregation.py` | `tests/cases/external/e2e/test_xdist_message_aggregation.py` | `external` | no | external, subprocess, xdist, Docker, or platform harness workflow |
| `tests/e2e/test_xdist_remote_message_aggregation.py` | `tests/cases/external/e2e/test_xdist_remote_message_aggregation.py` | `external` | no | external, subprocess, xdist, Docker, or platform harness workflow |
| `tests/feature/test_autoload.py` | `tests/cases/e2e/feature/test_autoload.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_batch_collection.py` | `tests/cases/e2e/feature/test_batch_collection.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_batch_threshold.py` | `tests/cases/integration/feature/test_batch_threshold.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_cucumber_json.py` | `tests/cases/e2e/feature/test_cucumber_json.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_e2e_benchmark.py` | `tests/cases/perf/feature/test_e2e_benchmark.py` | `perf` | no | benchmark-style performance probe |
| `tests/feature/test_empty_bdd_headings_validation.py` | `tests/cases/integration/feature/test_empty_bdd_headings_validation.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_foundation_cleanup.py` | `tests/cases/integration/feature/test_foundation_cleanup.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_gherkin_go_collection.py` | `tests/cases/e2e/feature/test_gherkin_go_collection.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_gherkin_terminal_reporter.py` | `tests/cases/e2e/feature/test_gherkin_terminal_reporter.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_heading_validation_snippet_boundaries.py` | `tests/cases/integration/feature/test_heading_validation_snippet_boundaries.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_http.py` | `tests/cases/e2e/feature/test_http.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_outline.py` | `tests/cases/integration/feature/test_outline.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_report.py` | `tests/cases/e2e/feature/test_report.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_report_context_hierarchy.py` | `tests/cases/e2e/feature/test_report_context_hierarchy.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_run_access_and_errors.py` | `tests/cases/integration/feature/test_run_access_and_errors.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_run_hooks.py` | `tests/cases/integration/feature/test_run_hooks.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_run_lifecycle.py` | `tests/cases/e2e/feature/test_run_lifecycle.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_run_lifecycle_integration.py` | `tests/cases/e2e/feature/test_run_lifecycle_integration.py` | `e2e` | yes | legacy feature integration file exercises full user-visible workflow coverage |
| `tests/feature/test_same_function_name.py` | `tests/cases/integration/feature/test_same_function_name.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_scenario_execution_edge_cases.py` | `tests/cases/integration/feature/test_scenario_execution_edge_cases.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_step_matching_ambiguous.py` | `tests/cases/integration/feature/test_step_matching_ambiguous.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_step_matching_priority.py` | `tests/cases/integration/feature/test_step_matching_priority.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_steps.py` | `tests/cases/integration/feature/test_steps.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/feature/test_xdist_parallel_integration.py` | `tests/cases/integration/feature/test_xdist_parallel_integration.py` | `integration` | no | local pytester/runtime/parser/plugin behavior flow |
| `tests/generation/test_generate.py` | `tests/cases/integration/generation/test_generate.py` | `integration` | yes | code generation behavior |
| `tests/generation/test_generate_missing.py` | `tests/cases/integration/generation/test_generate_missing.py` | `integration` | yes | code generation behavior |
| `tests/generation/test_template_packaging.py` | `tests/cases/contract/generation/test_template_packaging.py` | `contract` | yes | template packaging/generated artifact contract |
| `tests/gherkin_integration/test_pickles_load.py` | `tests/cases/integration/gherkin_integration/test_pickles_load.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_gherkin_message_reporter_pytest90_regression.py` | `tests/cases/integration/hook/test_gherkin_message_reporter_pytest90_regression.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_gherkin_reporter_context_lifecycle.py` | `tests/cases/integration/hook/test_gherkin_reporter_context_lifecycle.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_heading_validation_diagnostics.py` | `tests/cases/integration/hook/test_heading_validation_diagnostics.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_hook.py` | `tests/cases/integration/hook/test_hook.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_hook_run_regression.py` | `tests/cases/integration/hook/test_hook_run_regression.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_live_formatter_output_relay.py` | `tests/cases/integration/hook/test_live_formatter_output_relay.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_live_formatter_terminal_layout.py` | `tests/cases/integration/hook/test_live_formatter_terminal_layout.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_parse_error_sink.py` | `tests/cases/integration/hook/test_parse_error_sink.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_reporting_context_snapshot_unit.py` | `tests/cases/integration/hook/test_reporting_context_snapshot_unit.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_run_diagnostics.py` | `tests/cases/integration/hook/test_run_diagnostics.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_run_fixture_stash.py` | `tests/cases/integration/hook/test_run_fixture_stash.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_run_scenario_runtime_unit.py` | `tests/cases/integration/hook/test_run_scenario_runtime_unit.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_run_transitions.py` | `tests/cases/integration/hook/test_run_transitions.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_scenario_collection_read_hooks.py` | `tests/cases/integration/hook/test_scenario_collection_read_hooks.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_scenario_locator_pipeline.py` | `tests/cases/integration/hook/test_scenario_locator_pipeline.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/hook/test_scenario_reference_resolution.py` | `tests/cases/integration/hook/test_scenario_reference_resolution.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/library/test_parent.py` | `tests/cases/integration/library/test_parent.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/messages/test_capability_id_normalization.py` | `tests/cases/contract/messages/test_capability_id_normalization.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_coverage.py` | `tests/cases/contract/messages/test_coverage.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_execution_message_adapter.py` | `tests/cases/integration/messages/test_execution_message_adapter.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_execution_message_adapter_roundtrip.py` | `tests/cases/contract/messages/test_execution_message_adapter_roundtrip.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_governance.py` | `tests/cases/contract/messages/test_governance.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_governance_cli_contract.py` | `tests/cases/contract/messages/test_governance_cli_contract.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_attachments.py` | `tests/cases/integration/messages/test_message_attachments.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_message_baseline_diff.py` | `tests/cases/contract/messages/test_message_baseline_diff.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_capability_inventory.py` | `tests/cases/contract/messages/test_message_capability_inventory.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_emission_points.py` | `tests/cases/integration/messages/test_message_emission_points.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_message_extension.py` | `tests/cases/integration/messages/test_message_extension.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_message_governance_checklist.py` | `tests/cases/contract/messages/test_message_governance_checklist.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_outcome_mapping.py` | `tests/cases/integration/messages/test_message_outcome_mapping.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_message_status_governance.py` | `tests/cases/contract/messages/test_message_status_governance.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_typing_regression.py` | `tests/cases/contract/messages/test_message_typing_regression.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_message_validation.py` | `tests/cases/contract/messages/test_message_validation.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_messages.py` | `tests/cases/contract/messages/test_messages.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_messages_feature_suite.py` | `tests/cases/contract/messages/test_messages_feature_suite.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_startup_imports.py` | `tests/cases/integration/messages/test_startup_imports.py` | `integration` | yes | message runtime behavior closer to local integration than schema contract |
| `tests/messages/test_xdist_message_consolidation.py` | `tests/cases/contract/messages/test_xdist_message_consolidation.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages/test_xdist_remote_transport.py` | `tests/cases/contract/messages/test_xdist_remote_transport.py` | `contract` | no | cucumber messages schema, governance, stream, or output contract |
| `tests/messages_coverage/probes/test_failing_step_runtime.py` | `tests/cases/contract/messages_coverage/probes/test_failing_step_runtime.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/messages_coverage/probes/test_parse_error_runtime.py` | `tests/cases/contract/messages_coverage/probes/test_parse_error_runtime.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/messages_coverage/probes/test_undefined_parameter_runtime.py` | `tests/cases/contract/messages_coverage/probes/test_undefined_parameter_runtime.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/messages_coverage/test_full_capability_governance.py` | `tests/cases/contract/messages_coverage/test_full_capability_governance.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/messages_coverage/test_mandatory_attachments.py` | `tests/cases/contract/messages_coverage/test_mandatory_attachments.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/messages_coverage/test_run_governance_regression.py` | `tests/cases/contract/messages_coverage/test_run_governance_regression.py` | `contract` | no | messages capability coverage and mandatory output contract probes |
| `tests/model/test_cucumber_formatter_adapter.py` | `tests/cases/unit/model/test_cucumber_formatter_adapter.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/model/test_stash_access_maybe.py` | `tests/cases/unit/model/test_stash_access_maybe.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/scripts/test_spec_prefix_resolution.py` | `tests/cases/contract/scripts/test_spec_prefix_resolution.py` | `contract` | no | script output/schema contract verification |
| `tests/scripts/test_sync_messages_contract_schemas.py` | `tests/cases/contract/scripts/test_sync_messages_contract_schemas.py` | `contract` | no | script output/schema contract verification |
| `tests/struct_bdd/test_deserialization.py` | `tests/cases/integration/struct_bdd/test_deserialization.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/struct_bdd/test_gherkin_document_model_compat.py` | `tests/cases/integration/struct_bdd/test_gherkin_document_model_compat.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/struct_bdd/test_steps.py` | `tests/cases/integration/struct_bdd/test_steps.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/support/test_cucumber_formatters.py` | `tests/cases/contract/support/test_cucumber_formatters.py` | `contract` | yes | support helper contract or external platform harness |
| `tests/support/test_docker_wsl2.py` | `tests/cases/external/support/test_docker_wsl2.py` | `external` | yes | support helper contract or external platform harness |
| `tests/test_hooks.py` | `tests/cases/integration/test_hooks.py` | `integration` | no | local hook, parser, plugin, or runtime integration flow |
| `tests/test_utils.py` | `tests/cases/unit/test_utils.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/gherkin_document/test_feature_context_lookup.py` | `tests/cases/unit/unit/model/gherkin_document/test_feature_context_lookup.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_feature_binding.py` | `tests/cases/unit/unit/model/test_feature_binding.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_run.py` | `tests/cases/unit/unit/model/test_run.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_scenario_run.py` | `tests/cases/unit/unit/model/test_scenario_run.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_scenario_run_characterization.py` | `tests/cases/unit/unit/model/test_scenario_run_characterization.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_scenario_run_model.py` | `tests/cases/unit/unit/model/test_scenario_run_model.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/model/test_scenario_run_returns_contract.py` | `tests/cases/unit/unit/model/test_scenario_run_returns_contract.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/parser/test_parser_result_contract.py` | `tests/cases/unit/unit/parser/test_parser_result_contract.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/parser/test_parsers.py` | `tests/cases/unit/unit/parser/test_parsers.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_collector_batch.py` | `tests/cases/unit/unit/test_collector_batch.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_context_error_state.py` | `tests/cases/unit/unit/test_context_error_state.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_dead_code.py` | `tests/cases/unit/unit/test_dead_code.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_gherkin_go_bridge.py` | `tests/cases/unit/unit/test_gherkin_go_bridge.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_gherkin_go_fallback.py` | `tests/cases/unit/unit/test_gherkin_go_fallback.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_gherkin_go_parse.py` | `tests/cases/unit/unit/test_gherkin_go_parse.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_group_ordering.py` | `tests/cases/unit/unit/test_group_ordering.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_no_commented_code.py` | `tests/cases/unit/unit/test_no_commented_code.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_parsers_unit.py` | `tests/cases/unit/unit/test_parsers_unit.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_performance_batch.py` | `tests/cases/unit/unit/test_performance_batch.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_plugin_patterns.py` | `tests/cases/unit/unit/test_plugin_patterns.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_quality_gates.py` | `tests/cases/unit/unit/test_quality_gates.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_step_internals.py` | `tests/cases/unit/unit/test_step_internals.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_steps.py` | `tests/cases/unit/unit/test_steps.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_steps_given.py` | `tests/cases/unit/unit/test_steps_given.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_steps_unicode.py` | `tests/cases/unit/unit/test_steps_unicode.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
| `tests/unit/test_threshold_finder.py` | `tests/cases/unit/unit/test_threshold_finder.py` | `unit` | no | pure in-process/module-level checks or argument matcher behavior |
