"""Unified architecture tooling facade.

Provides a single entry point for all architecture-related operations:
  inject-source    Inject responsibility contracts + architecture scores into source files.
  inject-tests     Inject test responsibility templates into test functions.
  fill-tests       Fill placeholder values in injected test docstrings.
  collect-scores   Collect architecture scores from source docstrings.
  collect-test-scores  Collect test quality scores from test docstrings.
  analyze-gaps     Analyze weak responsibility-contract zones.

Configuration is read from [tool.architecture] in pyproject.toml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ── config loader ──────────────────────────────────────────────────────


def _load_arch_config() -> dict[str, Any]:
    """Read [tool.architecture] from pyproject.toml, returning defaults if absent."""
    try:
        pyproject = Path("pyproject.toml")
        if not pyproject.exists():
            return {}
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found, no-redef]
        except ImportError:
            return {}

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data.get("tool", {}).get("architecture", {})


def _merge_config(cli_args: dict[str, Any], section: str | None) -> dict[str, Any]:
    """Merge CLI args with pyproject.toml config (CLI wins)."""
    cfg = _load_arch_config()
    if section and section in cfg:
        sub = cfg[section]
    else:
        sub = cfg
    merged = dict(sub)
    for k, v in cli_args.items():
        if v is None or v == [] or v is False:
            continue
        if isinstance(v, list) and isinstance(merged.get(k), str):
            merged[k] = v[0] if len(v) == 1 else v
        else:
            merged[k] = v
    return merged


# ── subcommand: inject-source ──────────────────────────────────────────


def _cmd_inject_source(args: argparse.Namespace) -> int:
    from inject_responsibility_docstrings import build_report

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "inject_source",
    )
    root_val = cfg.get("root", "src/pytest_bdd")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    exclude = tuple(cfg.get("exclude", []))
    report, changed = build_report(root, check=args.check, write_stubs=args.stub, exclude=exclude)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and changed:
        print("Responsibility stubs are not filled.", file=sys.stderr)
        return 1
    return 0 if not report["errors"] else 2


# ── subcommand: inject-tests ───────────────────────────────────────────


def _cmd_inject_tests(args: argparse.Namespace) -> int:
    import inject_test_docstrings

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "inject_tests",
    )
    roots = cfg.get("root", [])
    if isinstance(roots, str):
        roots = [roots]
    if not roots:
        roots = ["src/pytest_bdd_testing", "tests"]
    exclude_names = set(cfg.get("exclude", []))
    force = args.force
    inject_test_docstrings.process_roots([Path(r) for r in roots], exclude_names, force=force)
    return 0


# ── subcommand: fill-tests ─────────────────────────────────────────────


def _cmd_fill_tests(args: argparse.Namespace) -> int:
    import fill_test_docstrings

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "fill_tests",
    )
    roots = cfg.get("root", [])
    if isinstance(roots, str):
        roots = [roots]
    if not roots:
        roots = ["src/pytest_bdd_testing", "tests"]
    exclude_names = set(cfg.get("exclude", []))
    fill_test_docstrings.process_roots([Path(r) for r in roots], exclude_names)
    return 0


# ── subcommand: collect-scores ─────────────────────────────────────────


def _cmd_collect_scores(args: argparse.Namespace) -> int:
    import collect_arch_scores

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "collect_scores",
    )
    root_val = cfg.get("root", "src/pytest_bdd")
    if isinstance(root_val, str):
        root_val = [root_val]
    roots = [Path(r) for r in root_val]
    exclude = tuple(cfg.get("exclude", []))
    entries = collect_arch_scores.collect_entries(roots, exclude=exclude)
    collect_arch_scores.write_json(entries)
    collect_arch_scores.write_markdown(entries)
    print(f"Scanned {len(entries)} entities.")
    documented = sum(1 for e in entries if e.documented)
    missing = sum(1 for e in entries if e.missing_sections)
    print(f"Documented: {documented}; missing sections: {missing}.")
    print("Output: docs/architecture/OBJECT_MAP.md")
    print("JSON: .planning/tmp/object-map.json")
    return 0


# ── subcommand: collect-test-scores ────────────────────────────────────


def _cmd_collect_test_scores(args: argparse.Namespace) -> int:
    import collect_test_scores

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "collect_test_scores",
    )
    roots = cfg.get("root", [])
    if isinstance(roots, str):
        roots = [roots]
    if not roots:
        roots = ["src/pytest_bdd_testing/cases", "tests"]
    exclude_names = set(cfg.get("exclude", []))
    entries = collect_test_scores.collect_entries([Path(r) for r in roots], exclude_names)
    collect_test_scores.write_report(entries)
    if entries:
        avg = sum(e.average for e in entries) / len(entries)
        print(f"Scanned {len(entries)} test entities; average score: {avg:.2f}")
    else:
        print("No test entities found.")
    return 0


# ── subcommand: analyze-gaps ───────────────────────────────────────────


def _cmd_analyze_gaps(args: argparse.Namespace) -> int:
    import analyze_responsibility_zones

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "analyze_gaps",
    )
    root_val = cfg.get("root", "src/pytest_bdd")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    entries_data = analyze_responsibility_zones.load_or_collect(root)
    zones = analyze_responsibility_zones.build_zones(entries_data)
    analyze_responsibility_zones.write_outputs(entries_data, zones)
    print(f"Analyzed {len(entries_data)} entities; found {len(zones)} problem zones.")
    print("Output: docs/architecture/RESPONSIBILITY_GAPS.md")
    return 0


# ── common arg builders ────────────────────────────────────────────────


def _add_inject_mode_args(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Check if stubs are filled (CI validation)")
    mode.add_argument("--stub", action="store_true", help="Inject blank templates for agent-driven filling")


def _add_no_mode_args(parser: argparse.ArgumentParser) -> None:
    """For commands that don't need --check/--write/--stub."""


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="Root directory to scan (repeatable; overrides config)",
    )
    parser.add_argument("--exclude", action="append", default=[], help="Directory name to exclude (repeatable)")


# ── subcommand: list-stubs ─────────────────────────────────────────────


def _cmd_list_stubs(args: argparse.Namespace) -> int:
    """List all stub templates that need agent filling, grouped by file."""
    import ast as _ast
    import re as _re

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "inject_source",
    )
    root_val = cfg.get("root", "src/pytest_bdd")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    exclude = tuple(cfg.get("exclude", []))

    stub_marker = _re.compile(r"<[1-5]-[1-5]>|<Describe|<Explain|<State|#arch-eval:\w+=<[1-5]-[1-5]>")

    results: list[dict] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or any(ex in path.parts for ex in exclude):
            continue
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in _ast.walk(tree):
            if isinstance(node, (_ast.Module, _ast.ClassDef, _ast.FunctionDef, _ast.AsyncFunctionDef)):
                doc = _ast.get_docstring(node, clean=False)
                if doc and stub_marker.search(doc):
                    if isinstance(node, _ast.Module):
                        kind = "module"
                        line = 1
                        name = path.stem
                    elif isinstance(node, _ast.ClassDef):
                        kind = "class"
                        line = node.lineno
                        name = node.name
                    else:
                        kind = "function" if isinstance(node, _ast.FunctionDef) else "async function"
                        line = node.lineno
                        name = node.name
                    results.append({
                        "file": path.as_posix(),
                        "line": line,
                        "kind": kind,
                        "name": name,
                        "has_stub_scores": "<1-5>" in doc or "<0-5>" in doc,
                        "has_stub_text": "<Describe" in doc or "<Explain" in doc or "<State" in doc,
                    })

    print(json.dumps({"stubs": results, "total": len(results)}, indent=2))
    return 0


# ── main ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified architecture tooling facade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Subcommands:
  inject-source       Inject responsibility contracts + architecture scores
  inject-tests        Inject test responsibility templates
  fill-tests          Fill placeholder values in test docstrings
  collect-scores      Collect architecture scores from docstrings
  collect-test-scores Collect test quality scores from docstrings
  analyze-gaps        Analyze weak responsibility-contract zones

Configuration: [tool.architecture] in pyproject.toml
  [tool.architecture.inject_source]
  root = "src/pytest_bdd"
  exclude = ["cases"]

  [tool.architecture.inject_tests]
  root = ["src/pytest_bdd_testing", "tests"]
  exclude = ["cases", "conftest"]
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # inject-source
    p_is = sub.add_parser("inject-source", help="Inject blank architecture templates (agent fills them)")
    _add_inject_mode_args(p_is)
    _add_common_args(p_is)

    # inject-tests
    p_it = sub.add_parser("inject-tests", help="Inject test responsibility templates")
    _add_common_args(p_it)
    p_it.add_argument("--force", action="store_true", help="Strip and re-inject even when templates already present")

    # fill-tests
    p_ft = sub.add_parser("fill-tests", help="Fill placeholder values in test docstrings")
    _add_common_args(p_ft)

    # collect-scores
    p_cs = sub.add_parser("collect-scores", help="Collect architecture scores from docstrings")
    _add_common_args(p_cs)

    # collect-test-scores
    p_cts = sub.add_parser("collect-test-scores", help="Collect test quality scores from docstrings")
    _add_common_args(p_cts)

    # analyze-gaps
    p_ag = sub.add_parser("analyze-gaps", help="Analyze weak responsibility-contract zones")
    _add_common_args(p_ag)

    # list-stubs
    p_ls = sub.add_parser("list-stubs", help="List all stub templates pending agent fill")
    _add_common_args(p_ls)

    args = parser.parse_args()

    # Normalize root/exclude from pyproject.toml lists: CLI --root appends to the list
    if isinstance(args.root, list) and len(args.root) == 0:
        args.root = None
    if isinstance(args.exclude, list) and len(args.exclude) == 0:
        args.exclude = None

    commands = {
        "inject-source": _cmd_inject_source,
        "inject-tests": _cmd_inject_tests,
        "fill-tests": _cmd_fill_tests,
        "collect-scores": _cmd_collect_scores,
        "collect-test-scores": _cmd_collect_test_scores,
        "analyze-gaps": _cmd_analyze_gaps,
        "list-stubs": _cmd_list_stubs,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
