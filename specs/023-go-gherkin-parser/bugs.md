# Bugs: Go Gherkin Parser (023)

## BUG-001: `serializeError` struct scoping prevents compilation [FIXED]

**Severity**: BLOCKER
**File**: `gherkin_go/bridge/bridge.go`
**Resolution**: Moved `source`, `location`, `parseError` structs to package level. Removed duplicate definitions from `serializeError()`.

## BUG-002: `_lib_error` global prevents retry after library becomes available [FIXED]

**Severity**: LOW (dev/test friction)
**File**: `src/pytest_bdd/_gherkin_go/_bridge.py`
**Resolution**: Added `_reset()` function for test/dev use. Hot-reload remains out of scope for production.

## BUG-003: `go.mod` messages v24 vs gherkin v28 version mismatch [FALSE POSITIVE]

**Severity**: BLOCKER → N/A
**Resolution**: `gherkin/go/v28` legitimately depends on `messages/go/v24`. Version numbers are independently assigned. `go mod tidy` confirmed correct resolution.

## BUG-004: Go `newId` uses UUID v4, may not match Python parser ID generation [FIXED]

**Severity**: MEDIUM
**File**: `gherkin_go/bridge/bridge.go`
**Resolution**: Replaced `uuid.Must(uuid.NewV4())` with `gherkin.NewIdGenerator()` which produces IDs matching Python's parser format. Removed `gofrs/uuid` direct import.

## BUG-005: `fork()` + cgo unsafe on Linux — multiprocessing deadlock/crash [FIXED]

**Severity**: BLOCKER
**File**: `src/pytest_bdd/collector_batch.py`
**Resolution**: Changed `Pool()` to `multiprocessing.get_context("spawn").Pool()` for safe cross-platform multiprocessing.

## BUG-006: Broad `Exception` catch in `_try_go_parse` silently swallows Go failures [FIXED]

**Severity**: MEDIUM
**File**: `src/pytest_bdd/collector_batch.py`
**Resolution**: Narrowed exception handling: `GherkinParseError` re-raised with URI injection, `GherkinGoNotAvailable` and `(OSError, RuntimeError)` fall back in auto mode. No broad `Exception` catch.

## BUG-007: Go `json.Marshal` field naming may not match Python `message_converter.from_dict()` expectations [PARTIALLY FIXED]

**Severity**: HIGH
**Resolution**: Added `_documents_equivalent()` normalization function and cross-backend comparison tests. Full fixture-based validation against `gherkin/testdata/good/` still needed once Go shared library is built.

## BUG-008: Go error response `source.uri` always empty — Python must inject file path [FIXED]

**Severity**: MEDIUM
**File**: `src/pytest_bdd/collector_batch.py` `_try_go_parse()`
**Resolution**: `_try_go_parse()` now catches `GherkinParseError`, injects `path` into each error's `source.uri`, then re-raises.

## BUG-009: `_should_use_go_backend()` duplicated in two modules [FIXED]

**Severity**: LOW
**Resolution**: Single source of truth in `_gherkin_go/__init__.py` as `should_use_go_backend()` and `is_strict_go_mode()`. `collector_batch.py` delegates to these.

## BUG-010: FR-009 "byte-identical" GherkinDocument is unrealistic [FIXED]

**Severity**: HIGH
**File**: `specs/023-go-gherkin-parser/spec.md`
**Resolution**: Changed FR-009 to "semantically equivalent after normalization". Changed SC-002 to "semantically equivalent parse results (after normalization)". Added `_documents_equivalent()` that strips `None` values and ignores `id` fields.

## BUG-011: Go markdown extraction may produce different Gherkin than Python/JS [FIXED]

**Severity**: HIGH
**File**: `src/pytest_bdd/collector_batch.py` `_parse_feature_file()`
**Resolution**: Added post-parse validation for `.feature.md` files: Go result compared against Python result via `_documents_equivalent()`. If they differ, Python result is used with WARNING log.

## BUG-012: Windows DLL loading fails if MinGW runtime DLLs not on PATH [FIXED]

**Severity**: BLOCKER
**File**: `src/pytest_bdd/_gherkin_go/_build.py`
**Resolution**: Added `-ldflags="-extldflags=-static"` to Windows Go build command, statically linking C runtime dependencies.

## BUG-013: `go.mod` never tidied — stale indirect dependency on messages/v24 [FALSE POSITIVE]

**Severity**: BLOCKER → N/A
**Resolution**: `go mod tidy && go mod vendor` run. `messages/go/v24` is correct transitive dependency of `gherkin/go/v28`. Removed unused `gofrs/uuid` direct import (now only indirect via messages).

## BUG-014: `FreeCString` nil pointer crash [FIXED]

**Severity**: MEDIUM
**File**: `gherkin_go/bridge/bridge.go`, `src/pytest_bdd/_gherkin_go/_bridge.py`
**Resolution**: Go `FreeCString` now nil-safe (`if s == nil { return }`). Python `gherkin_go_version()` returns early before try/finally when result is falsy, so `FreeCString` never receives nil.
