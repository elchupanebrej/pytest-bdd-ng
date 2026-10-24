from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

_Result = TypeVar("_Result")
_CONTINUATION_RELEASE_DELAY_SECONDS = 1.0


def main(argv: Sequence[str] | None = None) -> int:
    """Run mcp-pdb's registered tools over the advertised Streamable HTTP port."""
    parser = argparse.ArgumentParser(prog="pytest-cuke-debugger-mcp")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--inspection-url", required=True)
    args = parser.parse_args(argv)

    try:
        debugger = importlib.import_module("mcp_pdb.main")  # Keep this optional import inside the child process.
    except ImportError as error:
        parser.exit(2, f"pytest-cuke Debug MCP backend requires pytest-cuke[debug-mcp]: {error}\n")

    mcp = debugger.mcp
    install_debugger_continuation(mcp, debugger.send_pdb_command, args.inspection_url)
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    _configure_transport_security(mcp.settings, host=args.host, port=args.port)
    mcp.run(transport="streamable-http")
    return 0


def _configure_transport_security(settings: Any, *, host: str, port: int) -> None:
    """Keep the MCP SDK's rebinding allowlist aligned with the advertised bind address."""
    transport_security = getattr(settings, "transport_security", None)
    if transport_security is None:
        return

    bracketed_host = host if host.startswith("[") and host.endswith("]") else f"[{host}]" if ":" in host else host
    authority = f"{bracketed_host}:{port}"
    transport_security.allowed_hosts = [authority]
    transport_security.allowed_origins = [f"http://{authority}"]


def install_debugger_continuation(
    server: Any,
    send_pdb_command: Callable[[str], str],
    inspection_url: str,
) -> None:
    """Release the matching pytest failure when mcp-pdb continues execution."""
    original = send_pdb_command

    @wraps(original)
    def continue_and_release(command: str) -> str:
        failure: tuple[str, int] | None = None
        if _is_continue_command(command):
            try:
                failure = _active_failure(inspection_url)
            except Exception as error:
                print(
                    "pytest-cuke could not inspect the active failure before debugger continuation: "
                    f"{error}",
                    file=sys.stderr,
                )

        response = original(command)
        if failure is not None and _continuation_succeeded(response):
            session_id, sequence = failure
            timer = threading.Timer(
                _CONTINUATION_RELEASE_DELAY_SECONDS,
                _release_after_continuation,
                args=(inspection_url, session_id, sequence),
            )
            timer.daemon = True
            timer.start()
        return response

    server.remove_tool("send_pdb_command")
    server.add_tool(continue_and_release, name="send_pdb_command", description=getattr(original, "__doc__", None))


def _is_continue_command(command: str) -> bool:
    return command.strip().lower() in {"c", "continue"}


def _continuation_succeeded(response: object) -> bool:
    if not isinstance(response, str):
        return False
    failed_prefixes = (
        "No active debugging session.",
        "Remote debugging connection closed.",
        "The debugging session appears to have ended.",
        "Error sending command:",
    )
    return not response.lstrip().startswith(failed_prefixes)


def _active_failure(inspection_url: str) -> tuple[str, int] | None:
    result = _call_inspection_tool(inspection_url, "inspect_failure", {})
    failure = result.get("active_failure")
    session_id = result.get("session_id")
    if (
        not isinstance(failure, dict)
        or not isinstance(session_id, str)
        or not session_id
        or isinstance(failure.get("sequence"), bool)
        or not isinstance(failure.get("sequence"), int)
        or failure["sequence"] < 1
    ):
        return None
    return session_id, failure["sequence"]


def _release_after_continuation(inspection_url: str, session_id: str, sequence: int) -> None:
    """Release after the debugger tool has returned its response to the MCP client."""
    try:
        released = _call_inspection_tool(
            inspection_url,
            "release_failure",
            {"session_id": session_id, "sequence": sequence, "reason": "debugger_continuation"},
        )
        if released.get("released") is not True:
            raise RuntimeError(f"inspection server returned an invalid release result: {released!r}")
    except Exception as error:
        print(
            "pytest-cuke could not release the active failure after debugger continuation: "
            f"{error}",
            file=sys.stderr,
        )


def _call_inspection_tool(endpoint: str, name: str, arguments: dict[str, object]) -> dict[str, object]:
    """Call pytest's inspection server without letting debugger calls alter other holds."""
    from mcp import ClientSession  # noqa: PLC0415  # Keep optional MCP imports inside selected backend use.
    from mcp.client.streamable_http import streamable_http_client  # noqa: PLC0415

    async def call() -> dict[str, object]:
        async with (
            streamable_http_client(endpoint, terminate_on_close=False) as (read_stream, write_stream, _session_id),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if getattr(result, "isError", False):
                raise RuntimeError(f"inspection tool {name!r} failed: {result!r}")
            payload = getattr(result, "structuredContent", None)
            if isinstance(payload, dict):
                return payload
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        decoded = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(decoded, dict):
                        return decoded
            raise RuntimeError(f"inspection tool {name!r} returned no structured JSON: {result!r}")

    return _run_coroutine(call, timeout=5.0)


def _run_coroutine(factory: Callable[[], Awaitable[_Result]], *, timeout: float | None = None) -> _Result:
    def run_call() -> _Result:
        async def call() -> _Result:
            if timeout is None:
                return await factory()
            return await asyncio.wait_for(factory(), timeout=timeout)

        return asyncio.run(call())

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return run_call()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="pytest-cuke-debug-mcp-client") as executor:
        return executor.submit(run_call).result()


if __name__ == "__main__":
    raise SystemExit(main())
