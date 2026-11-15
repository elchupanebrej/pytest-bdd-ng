"""Render a saved Cucumber Messages stream into one HTML document."""

from __future__ import annotations

import sys

from pytest_cuke.html_report import render_cucumber_html


def main() -> int:
    """Read NDJSON envelopes from stdin and write the HTML document to stdout."""
    lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
    if not lines:
        print("pytest-cuke html replay: empty Messages stream", file=sys.stderr)
        return 1
    try:
        html = render_cucumber_html(",".join(lines))
    except Exception as error:
        print(f"pytest-cuke html replay: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
