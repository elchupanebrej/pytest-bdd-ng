"""Compatibility wrapper for the importable quality gates module."""

from __future__ import annotations

from importlib import import_module

if __name__ == "__main__":
    main = import_module("pytest_bdd._ruff.rules.quality_gates").main
    raise SystemExit(main())
