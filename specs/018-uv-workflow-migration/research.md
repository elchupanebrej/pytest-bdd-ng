# Research Notes

**Branch**: `018-uv-workflow-migration`

## Resolved Technical Unknowns

- **Decision**: Replace `conda` completely globally. Use `uv python install`. Ensure `uv` is tracked directly in `pyproject.toml` [project.optional-dependencies] `testenv` subset so tests properly enforce constraints decoupled from core execution.
- **Decision**: Execution of local tool scripts (e.g. `validate_feature_headings`) will occur natively by registering them as entrypoints within `[project.scripts]` in `pyproject.toml` instead of relying on explicit `uv run python script.py` cascades.
- **Rationale**: The specification defines `uv` exclusively for test contexts over foundational integration. Modifying endpoints correctly ensures local `uv run validate_feature_headings` and `.github` hooks process effortlessly without edge-case setups.
- **Alternatives Considered**: Modifying Markdown / RST docs to explicitly inject `uv run script.py`. Rejected because entrypoints elegantly simplify interface logic and ensure isolated testing constraints.
