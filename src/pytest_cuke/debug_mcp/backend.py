from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run mcp-pdb's registered tools over the advertised Streamable HTTP port."""
    parser = argparse.ArgumentParser(prog="pytest-cuke-debugger-mcp")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args(argv)

    try:
        from mcp_pdb.main import mcp  # noqa: PLC0415  # Import the optional backend only in the selected child process.
    except ImportError as error:
        parser.exit(2, f"pytest-cuke Debug MCP backend requires pytest-cuke[debug-mcp]: {error}\n")

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
