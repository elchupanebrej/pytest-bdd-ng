# Research Questions

## Cucumber JSON unification

- **Can the legacy `LogBDDCucumberJSON` accept an externally-provided path without refactoring its internal write logic?** It currently reads `cucumber_json_path` itself via `config.getini()`. When the dispatcher activates the `builtin` engine, can it pass the path directly into the legacy plugin constructor, or does `CucumberJsonPlugin.__init__` need to change?

## Phase 20 debug MCP

- **What public import/runtime APIs does `mcp-pdb` expose for embedding inside a pytest plugin?** Verify whether pytest-bdd-ng can start and manage remote debug sessions through library APIs, or whether it must invoke/compose the documented CLI and `rpdb` entry points.
