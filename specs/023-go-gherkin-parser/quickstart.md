# Quickstart: Go Gherkin Parser

**Feature**: Go Gherkin Parser (023-go-gherkin-parser)

## For End Users

### Installation

```bash
pip install pytest-bdd-ng
```

If your platform has a prebuilt wheel with Go parser, it activates automatically (default `auto` mode). No configuration needed.

### Verify Go Parser is Active

```bash
PYTEST_BDD_GHERKIN_BACKEND=auto pytest --collect-only 2>&1 | grep "Using Go gherkin parser"
# Output: INFO: Using Go gherkin parser v28.1.0
```

### Explicit Backend Control

```bash
# Force Python parser
PYTEST_BDD_GHERKIN_BACKEND=python pytest

# Force Go parser (fail if unavailable)
PYTEST_BDD_GHERKIN_BACKEND=go pytest

# Auto (default): Go if available, Python fallback
PYTEST_BDD_GHERKIN_BACKEND=auto pytest
```

### Troubleshooting

If Go parser is not used despite `auto` mode:
1. Check `pip show pytest-bdd-ng` — ensure wheel has native extension (`.so`/`.dll`/`.dylib` in package)
2. Check platform compatibility — if your OS/arch differs from build machine, Go library won't load
3. Run with `PYTEST_BDD_GHERKIN_BACKEND=python` to force Python parser if Go causes issues

## For Contributors / Maintainers

### Prerequisites

- Go 1.21+ on PATH
- Python 3.10+ with `uv`
- Existing pytest-bdd development environment

### Building with Go Parser

```bash
# Clone with submodules (if used)
git clone --recurse-submodules <repo>

# Install with Go build step
uv pip install -e .

# Build wheel with Go parser
uv run python -m build
```

### Vendoring Go Dependencies

```bash
cd gherkin_go
go mod tidy
go mod vendor
cd ..
git add gherkin_go/vendor/
```

### Running Tests

```bash
# Full test suite with Go parser
PYTEST_BDD_GHERKIN_BACKEND=auto uv run pytest tests/

# Cross-backend comparison tests
uv run pytest tests/unit/test_gherkin_go_parse.py -v

# Build tests (verify Go compilation)
uv run pytest tests/build/test_gherkin_go_build.py -v
```

### Key Files

| File | Purpose |
|------|---------|
| `gherkin_go/bridge/bridge.go` | Go C-exported functions |
| `src/pytest_bdd/_gherkin_go/__init__.py` | Public Python API |
| `src/pytest_bdd/_gherkin_go/_bridge.py` | ctypes wrapper |
| `src/pytest_bdd/_gherkin_go/_build.py` | setuptools build command |
| `src/pytest_bdd/collector_batch.py` | Backend selection logic |

### CI Notes

- CI matrix must include `go-version: '1.21'` in `setup-go` action
- Windows CI needs `CGO_ENABLED=1` and a C compiler (MSYS2/MinGW or Visual Studio)
- Wheels without Go parser (no Go on build machine) are valid and tested in fallback mode
