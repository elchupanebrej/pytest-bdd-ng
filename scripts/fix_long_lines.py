"""Fix E501 line-too-long in docstrings — line-based state machine."""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


def _line_length_from_ruff_config() -> int:
    config_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if config_path.is_file():
        with config_path.open("rb") as fh:
            data = tomllib.load(fh)
        return data.get("tool", {}).get("ruff", {}).get("line-length", 120)
    return 120


LINE_LIMIT = _line_length_from_ruff_config()


def _wrap_line(text: str, indent: str) -> str:
    """Wrap a single long line to fit within LINE_LIMIT, preserving indent."""
    if re.match(r"^\s*#arch-eval:", text) or re.match(r"^\s*#test-eval:", text):
        return text
    width = max(80, LINE_LIMIT - len(indent))
    wrapped = textwrap.wrap(text.strip(), width=width, break_long_words=False)
    return "\n".join(indent + w for w in wrapped)


def fix_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    result: list[str] = []
    in_docstring = False
    docstring_quote: str | None = None
    changed = False

    for line in lines:
        stripped = line.strip()

        if not in_docstring:
            m = re.match(r"^(\s*)(r?\"\"\"|\'\'\')", line)
            if m:
                quote = m.group(2)
                rest = line[m.end() :]
                close_idx = rest.find(quote)
                if close_idx != -1:
                    # Single-line docstring
                    if len(line) > LINE_LIMIT:
                        indent = m.group(1)
                        body = rest[:close_idx]
                        after = rest[close_idx + len(quote) :]
                        inner = indent + "    "
                        result.append(f"{indent}{quote}")
                        for bl in body.splitlines():
                            result.append(inner + bl.strip())
                        closer = f"{indent}{quote}{after}" if after else f"{indent}{quote}"
                        result.append(closer)
                        changed = True
                    else:
                        result.append(line)
                else:
                    result.append(line)
                    in_docstring = True
                    docstring_quote = quote
            else:
                result.append(line)
        else:
            # Inside docstring — check for close first
            close_idx = line.find(docstring_quote)
            if close_idx != -1:
                after = line[close_idx + len(docstring_quote) :]
                if len(line) > LINE_LIMIT and close_idx > 0:
                    indent = re.match(r"^(\s*)", line).group(1)
                    inner = line[:close_idx].rstrip()
                    result.extend(_wrap_line(inner, indent).splitlines())
                    close_line = f"{indent}{docstring_quote}{after}" if after else f"{indent}{docstring_quote}"
                    result.append(close_line)
                    changed = True
                else:
                    result.append(line)
                in_docstring = False
                docstring_quote = None
            elif len(stripped) > LINE_LIMIT:
                indent = re.match(r"^(\s*)", line).group(1)
                result.extend(_wrap_line(stripped, indent).splitlines())
                changed = True
            else:
                result.append(line)

    if changed:
        path.write_text("\n".join(result) + ("\n" if source.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> int:
    import argparse as _ap

    p = _ap.ArgumentParser()
    p.add_argument("root", nargs="+")
    p.add_argument("--limit", type=int, default=LINE_LIMIT)
    args = p.parse_args()

    import fix_long_lines as _s

    _s.LINE_LIMIT = args.limit

    fixed = 0
    for root_str in args.root:
        root = Path(root_str)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                if fix_file(path):
                    fixed += 1
                    print(f"Fixed: {path}")
            except Exception as exc:
                print(f"Error: {path}: {exc}", file=sys.stderr)

    print(f"\nFixed {fixed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
