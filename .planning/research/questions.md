# Research Questions

## Cucumber JSON unification

- **Can the legacy `LogBDDCucumberJSON` accept an externally-provided path without refactoring its internal write logic?** It currently reads `cucumber_json_path` itself via `config.getini()`. When the dispatcher activates the `builtin` engine, can it pass the path directly into the legacy plugin constructor, or does `CucumberJsonPlugin.__init__` need to change?
