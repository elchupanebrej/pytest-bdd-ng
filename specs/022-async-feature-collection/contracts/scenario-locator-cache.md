# Contract: FileScenarioLocator Cache Integration

**Feature**: 022-async-feature-collection
**Version**: 1.0

## Change Summary

`FileScenarioLocator` accepts an optional `cache` parameter. When provided and a path is found in cache, the locator skips file I/O and Gherkin parsing for that path.

## Interface Change

### Constructor

```python
class FileScenarioLocator:
    def __init__(
        self,
        *args,
        cache: dict[Path, GherkinDocument] | None = None,
        **kwargs,
    ):
```

**New parameter**: `cache` — optional dict mapping file paths to pre-parsed `GherkinDocument` instances.

### `resolve_features()` logic change

```python
for path in self._resolved_feature_paths:
    if self._cache and path in self._cache:
        gherkin_document = self._cache[path]
    else:
        content = path.read_text(encoding="utf-8")
        gherkin_document = parser.parse(content)
    # ... rest of pipeline unchanged
```

## Backward Compatibility

- `cache=None` (default): behavior identical to current implementation.
- Existing callers (`scenario(...)` decorator, `UrlScenarioLocator`) are unaffected.
- Only `FeatureFileModule._build_test_module()` passes the cache dict.

## Caller (FeatureFileModule._build_test_module)

```python
def _build_test_module(self, path, features_path_type, base_dir):
    batch_parser = FeatureBatchParser.find_in_stash(self.config.stash)
    cache = {self.get_path(): batch_parser.get(self.get_path())} if batch_parser and batch_parser._flushed else None
    module.test_scenarios = scenarios(
        *((path,) if path is not None else []),
        ...
        cache=cache,  # NEW
    )
```

**Constraint**: `cache` is only injected for auto-discovered `.feature` files (the `FeatureFileModule` path), never for `@scenario()` decorator invocations or URL-based locators.
