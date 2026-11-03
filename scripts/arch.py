"""Unified architecture tooling facade.

Provides a single entry point for all architecture-related operations:
  inject-source       Inject responsibility contracts + architecture scores into source files.
  inject-tests        Inject test responsibility templates into test functions.
  collect-scores      Collect architecture scores from source docstrings.
  collect-test-scores Collect test quality scores from test docstrings.
  analyze-gaps        Analyze weak responsibility-contract zones.
  list-stubs          List all stub templates pending agent fill.
  fix-long-lines      Fix E501 line-too-long in docstrings.
  fix-incomplete-scores Fix incomplete architecture score blocks.

Configuration is read from [tool.architecture] in pyproject.toml.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


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
    root_val = cfg.get("root", "src/pytest_cuke")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    exclude = tuple(cfg.get("exclude", []))
    report, changed = build_report(root, check=args.check, write_stubs=args.stub, exclude=exclude)

    if getattr(args, "markdown", False):
        lines = [
            "# Inject Source Report",
            "",
            f"- Files scanned: {report['files_scanned']}",
            f"- Docstrings added: {report['docstrings_added']}",
            f"- Docstrings updated: {report['docstrings_updated']}",
            f"- Already present: {report['already_present']}",
            f"- Pending fill: {report['pending_fill']}",
            f"- Missing: {report['missing']}",
            f"- Errors: {len(report['errors'])}",
        ]
        print("\n".join(lines))
    else:
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
        roots = ["tests"]
    exclude_names = set(cfg.get("exclude", []))
    force = args.force
    inject_test_docstrings.process_roots([Path(r) for r in roots], exclude_names, force=force)
    return 0


# ── subcommand: collect-scores ─────────────────────────────────────────


def _cmd_collect_scores(args: argparse.Namespace) -> int:
    import collect_arch_scores

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "collect_scores",
    )
    root_val = cfg.get("root", "src/pytest_cuke")
    if isinstance(root_val, str):
        root_val = [root_val]
    roots = [Path(r) for r in root_val]
    exclude = tuple(cfg.get("exclude", []))
    entries = collect_arch_scores.collect_entries(roots, exclude=exclude)
    collect_arch_scores.write_json(entries)
    collect_arch_scores.write_markdown(entries)

    if getattr(args, "json", False):
        if collect_arch_scores.OBJECT_MAP_JSON.exists():
            print(collect_arch_scores.OBJECT_MAP_JSON.read_text(encoding="utf-8").rstrip())
        else:
            payload = [{**asdict(e), "average": round(e.average, 2), "documented": e.documented} for e in entries]
            print(json.dumps(payload, indent=2, sort_keys=True))
    elif getattr(args, "markdown", False):
        if collect_arch_scores.OBJECT_MAP_MD.exists():
            print(collect_arch_scores.OBJECT_MAP_MD.read_text(encoding="utf-8").rstrip())
        else:
            documented = sum(1 for e in entries if e.documented)
            print(f"# Architecture Scores\n\nTotal: {len(entries)}\nDocumented: {documented}")
    else:
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
        roots = ["tests"]
    exclude_names = set(cfg.get("exclude", []))
    entries = collect_test_scores.collect_entries([Path(r) for r in roots], exclude_names)
    collect_test_scores.write_report(entries)

    if getattr(args, "json", False):
        if collect_test_scores.TEST_REPORT_JSON.exists():
            print(collect_test_scores.TEST_REPORT_JSON.read_text(encoding="utf-8").rstrip())
        else:
            print(json.dumps([asdict(e) for e in entries], indent=2))
    elif getattr(args, "markdown", False):
        avg = (sum(e.average for e in entries) / len(entries)) if entries else 0.0
        lines = [
            "# Test Quality Scores",
            "",
            f"- Total test entities: {len(entries)}",
            f"- Average score: {avg:.2f}",
            "",
            "| Entity | Target | Type | Isolation | Determinism | Setup | Assertions | Average |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for e in entries:
            lines.append(
                f"| `{e.file}` | {e.target} | {e.test_type} | "
                f"{e.scores.get('isolation', 'N/A')} | {e.scores.get('determinism', 'N/A')} | "
                f"{e.scores.get('setup_complexity', 'N/A')} | {e.scores.get('assertions_clarity', 'N/A')} | "
                f"{e.average:.2f} |"
            )
        print("\n".join(lines))
    else:
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
    root_val = cfg.get("root", "src/pytest_cuke")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    entries_data = analyze_responsibility_zones.load_or_collect(root)
    zones = analyze_responsibility_zones.build_zones(entries_data)
    analyze_responsibility_zones.write_outputs(entries_data, zones)

    if getattr(args, "json", False):
        if analyze_responsibility_zones.GAPS_JSON.exists():
            print(analyze_responsibility_zones.GAPS_JSON.read_text(encoding="utf-8").rstrip())
        else:
            print(json.dumps({"zones": zones}, indent=2, sort_keys=True))
    elif getattr(args, "markdown", False):
        if analyze_responsibility_zones.GAPS_MD.exists():
            print(analyze_responsibility_zones.GAPS_MD.read_text(encoding="utf-8").rstrip())
        else:
            print(f"# Responsibility Gaps\n\nProblem zones: {len(zones)}")
    else:
        print(f"Analyzed {len(entries_data)} entities; found {len(zones)} problem zones.")
        print("Output: docs/architecture/RESPONSIBILITY_GAPS.md")
    return 0


# ── subcommand: list-stubs ─────────────────────────────────────────────


def _cmd_list_stubs(args: argparse.Namespace) -> int:
    """List all stub templates that need agent filling, grouped by file."""
    import ast as _ast
    import re as _re

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "inject_source",
    )
    root_val = cfg.get("root", "src/pytest_cuke")
    if isinstance(root_val, list):
        root_val = root_val[0]
    root = Path(root_val)
    exclude = tuple(cfg.get("exclude", []))

    stub_marker = _re.compile(r"<[1-5]-[1-5]>|<Describe|<Explain|<State|#arch-eval:\w+=<[1-5]-[1-5]>")

    results: list[dict[str, Any]] = []
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

    if getattr(args, "markdown", False):
        lines = [
            f"# Responsibility Stubs ({len(results)} total)",
            "",
            "| File | Line | Kind | Name | Has Scores | Has Text |",
            "|---|---:|---|---|---|---|",
        ]
        for r in results:
            lines.append(
                f"| `{r['file']}` | {r['line']} | {r['kind']} | `{r['name']}` | "
                f"{r['has_stub_scores']} | {r['has_stub_text']} |"
            )
        print("\n".join(lines))
    else:
        print(json.dumps({"stubs": results, "total": len(results)}, indent=2))
    return 0


# ── subcommand: fix-long-lines ─────────────────────────────────────────


def _cmd_fix_long_lines(args: argparse.Namespace) -> int:
    import fix_long_lines

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "fix_long_lines",
    )
    roots = cfg.get("root", ["src/pytest_cuke"])
    if isinstance(roots, str):
        roots = [roots]
    exclude = set(cfg.get("exclude", []))
    limit = getattr(args, "limit", None) or fix_long_lines.LINE_LIMIT
    fix_long_lines.LINE_LIMIT = limit

    fixed_files: list[str] = []
    for root_str in roots:
        root = Path(root_str)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts or any(ex in path.parts for ex in exclude):
                continue
            try:
                if fix_long_lines.fix_file(path):
                    fixed_files.append(path.as_posix())
            except Exception as exc:
                print(f"Error: {path}: {exc}", file=sys.stderr)

    if getattr(args, "json", False):
        print(json.dumps({"fixed_count": len(fixed_files), "fixed_files": fixed_files}, indent=2))
    elif getattr(args, "markdown", False):
        lines = [f"# Fix Long Lines\n\nFixed {len(fixed_files)} files.\n"]
        for f in fixed_files:
            lines.append(f"- `{f}`")
        print("\n".join(lines))
    else:
        for f in fixed_files:
            print(f"Fixed: {f}")
        print(f"\nFixed {len(fixed_files)} files.")
    return 0


# ── subcommand: fix-incomplete-scores ──────────────────────────────────


def _cmd_fix_incomplete_scores(args: argparse.Namespace) -> int:
    import fix_incomplete_scores

    cfg = _merge_config(
        {"root": args.root, "exclude": args.exclude},
        "fix_incomplete_scores",
    )
    fixes = {
        Path("src/pytest_cuke/script/_feature_tree.py"): {
            "reason_for_existence": 4,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 4,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4,
            "entity_fullness": 2,
            "locational_stability": 4,
        },
        Path("src/pytest_cuke/script/validate_feature_headings.py"): {
            "reason_for_existence": 3,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 4,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4,
            "entity_fullness": 2,
            "locational_stability": 4,
        },
    }
    total = 0
    results: dict[str, int] = {}
    for path, defaults in fixes.items():
        if not path.exists():
            continue
        n = fix_incomplete_scores.fix_file(path, defaults)
        results[str(path)] = n
        total += n

    if getattr(args, "json", False):
        print(json.dumps({"total_fixed": total, "details": results}, indent=2))
    elif getattr(args, "markdown", False):
        lines = [f"# Fix Incomplete Scores\n\nTotal: {total} blocks fixed.\n"]
        for p, count in results.items():
            lines.append(f"- `{p}`: {count} blocks fixed")
        print("\n".join(lines))
    else:
        for p, count in results.items():
            print(f"  {p}: {count} blocks fixed")
        print(f"Total: {total} blocks fixed")
    return 0


# ── common arg builders ────────────────────────────────────────────────


def _add_inject_mode_args(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Check if stubs are filled (CI validation)")
    mode.add_argument("--stub", action="store_true", help="Inject blank templates for agent-driven filling")


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="Root directory to scan (repeatable; overrides config)",
    )
    parser.add_argument("--exclude", action="append", default=[], help="Directory name to exclude (repeatable)")
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="Format output as JSON")
    fmt.add_argument("--markdown", action="store_true", help="Format output as Markdown")


# ── main ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified architecture tooling facade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Subcommands:
  inject-source         Inject responsibility contracts + architecture scores
  inject-tests          Inject test responsibility templates
  collect-scores        Collect architecture scores from docstrings
  collect-test-scores   Collect test quality scores from docstrings
  analyze-gaps          Analyze weak responsibility-contract zones
  list-stubs            List all stub templates pending agent fill
  fix-long-lines        Fix line-too-long in docstrings
  fix-incomplete-scores Fix incomplete architecture score blocks

Configuration: [tool.architecture] in pyproject.toml
  [tool.architecture.inject_source]
  root = "src/pytest_cuke"
  exclude = ["cases"]

  [tool.architecture.inject_tests]
  root = ["tests"]
  exclude = ["cases", "conftest"]
""",
    )
    # Global formatting flags fallback
    parser.add_argument("--json", action="store_true", dest="global_json", help="Format output as JSON")
    parser.add_argument("--markdown", action="store_true", dest="global_markdown", help="Format output as Markdown")

    sub = parser.add_subparsers(dest="command", required=True)

    # inject-source
    p_is = sub.add_parser("inject-source", help="Inject blank architecture templates (agent fills them)")
    _add_inject_mode_args(p_is)
    _add_common_args(p_is)

    # inject-tests
    p_it = sub.add_parser("inject-tests", help="Inject test responsibility templates")
    _add_common_args(p_it)
    p_it.add_argument("--force", action="store_true", help="Strip and re-inject even when templates already present")

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

    # fix-long-lines
    p_fll = sub.add_parser("fix-long-lines", help="Fix line-too-long in docstrings")
    _add_common_args(p_fll)
    p_fll.add_argument("--limit", type=int, default=None, help="Maximum line length")

    # fix-incomplete-scores
    p_fis = sub.add_parser("fix-incomplete-scores", help="Fix incomplete architecture score blocks")
    _add_common_args(p_fis)

    args = parser.parse_args()

    # Propagate global formatting flags if subparser flags not set
    if getattr(args, "global_json", False) and not getattr(args, "json", False):
        args.json = True
    if getattr(args, "global_markdown", False) and not getattr(args, "markdown", False):
        args.markdown = True

    # Normalize root/exclude from pyproject.toml lists: CLI --root appends to the list
    if isinstance(args.root, list) and len(args.root) == 0:
        args.root = None
    if isinstance(args.exclude, list) and len(args.exclude) == 0:
        args.exclude = None

    commands = {
        "inject-source": _cmd_inject_source,
        "inject-tests": _cmd_inject_tests,
        "collect-scores": _cmd_collect_scores,
        "collect-test-scores": _cmd_collect_test_scores,
        "analyze-gaps": _cmd_analyze_gaps,
        "list-stubs": _cmd_list_stubs,
        "fix-long-lines": _cmd_fix_long_lines,
        "fix-incomplete-scores": _cmd_fix_incomplete_scores,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
