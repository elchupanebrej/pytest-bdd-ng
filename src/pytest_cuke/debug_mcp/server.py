from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import threading
import time
from contextlib import suppress
from importlib.util import find_spec
from typing import Any  # FastMCP resolves tool annotations at runtime.

from pydantic import ValidationError

from pytest_cuke.debug_mcp.artifacts import ArtifactSink, ArtifactWriteResult, validation_error_payload
from pytest_cuke.debug_mcp.schemas import BddMetadata, InvestigationArtifact
from pytest_cuke.debug_mcp.state import FailureHoldError, FailureQueue, ReleaseReason


class _ArtifactFailureMismatch(ValueError):
    """A submitted artifact does not describe the active held failure."""

class DebugMcpDependencyError(RuntimeError):
    """The selected optional Debug MCP backend is not installed or cannot start."""


def allocate_port(host: str, *, excluding: set[int] | None = None) -> int:
    """Ask the operating system for a currently free TCP port on the selected interface."""
    excluded = excluding or set()
    bind_host = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    family = socket.AF_INET6 if ":" in bind_host else socket.AF_INET
    for _ in range(20):
        with socket.socket(family, socket.SOCK_STREAM) as listener:
            listener.bind((bind_host, 0))
            port = int(listener.getsockname()[1])
        if port not in excluded:
            return port
    raise DebugMcpDependencyError(f"could not allocate a free Debug MCP port for host {host!r}")


def endpoint_url(host: str, port: int) -> str:
    url_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"http://{url_host}:{port}/mcp"


def ensure_optional_dependencies() -> None:
    """Check optional packages only after the user selects Debug MCP."""
    missing = [name for name in ("mcp", "mcp_pdb", "uvicorn") if find_spec(name) is None]
    if missing:
        names = ", ".join(missing)
        raise DebugMcpDependencyError(
            f"Debug MCP needs the optional dependencies {names}; install pytest-cuke[debug-mcp]"
        )


def probe_mcp_endpoint(endpoint: str, *, timeout: float = 2.0) -> None:
    """Complete a real MCP initialize handshake before publishing an endpoint."""
    from mcp import ClientSession  # noqa: PLC0415  # Keep the optional MCP SDK inert unless Debug MCP is selected.
    from mcp.client.streamable_http import streamable_http_client  # noqa: PLC0415

    async def initialize() -> None:
        async with (
            streamable_http_client(endpoint) as (read_stream, write_stream, _session_id),
            ClientSession(read_stream, write_stream) as client,
        ):
            await client.initialize()

    try:
        asyncio.run(asyncio.wait_for(initialize(), timeout=timeout))
    except Exception as error:
        detail = f"{type(error).__name__}: {error!r}"
        message = f"MCP endpoint did not complete initialization at {endpoint}: {detail}"
        raise DebugMcpDependencyError(message) from error


class DebuggerMcpProcess:
    """Manage the optional mcp-pdb HTTP server process and drain its stderr pipe."""

    def __init__(self, *, host: str, port: int, inspection_endpoint: str) -> None:
        self.host = host
        self.port = port
        self.inspection_endpoint = inspection_endpoint
        self.endpoint = endpoint_url(host, port)
        self.process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._stderr_tail: list[str] = []
        self._stderr_lock = threading.Lock()

    def start(self, *, timeout: float = 20.0) -> None:
        command = [
            sys.executable,
            "-m",
            "pytest_cuke.debug_mcp.backend",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--inspection-url",
            self.inspection_endpoint,
        ]
        try:
            process = subprocess.Popen(  # noqa: S603  # Fixed module entry point, argument list and no shell.
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            raise DebugMcpDependencyError(f"could not start mcp-pdb debugger server: {error}") from error
        self.process = process
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            name="pytest-cuke-debug-mcp-stderr",
            daemon=True,
        )
        self._stderr_thread.start()

        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise DebugMcpDependencyError(self._startup_error("mcp-pdb debugger server exited during startup"))
            try:
                probe_mcp_endpoint(self.endpoint, timeout=min(3.0, max(0.1, deadline - time.monotonic())))
                return
            except Exception as error:
                last_error = error
                time.sleep(0.1)
        detail = f": {type(last_error).__name__}: {last_error!r}" if last_error is not None else ""
        raise DebugMcpDependencyError(self._startup_error(f"mcp-pdb debugger server did not become ready{detail}"))

    def close(self, *, timeout: float = 2.0) -> None:
        process = self.process
        if process is None:
            return
        try:
            if process.poll() is None:
                with suppress(OSError):
                    process.terminate()
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    with suppress(OSError):
                        process.kill()
                    process.wait(timeout=timeout)
        finally:
            if process.stderr is not None:
                with suppress(OSError, ValueError):
                    process.stderr.close()
            if self._stderr_thread is not None:
                self._stderr_thread.join(timeout=timeout)
            self.process = None
        if process.poll() is None:
            raise DebugMcpDependencyError("mcp-pdb debugger process did not stop after terminate and kill")

    def _drain_stderr(self) -> None:
        process = self.process
        stream = process.stderr if process is not None else None
        if stream is None:
            return
        try:
            for line in stream:
                with self._stderr_lock:
                    self._stderr_tail.append(line.rstrip())
                    del self._stderr_tail[:-30]
        except (OSError, ValueError):
            return

    def _startup_error(self, message: str) -> str:
        with self._stderr_lock:
            detail = "\n".join(self._stderr_tail).strip()
        return f"{message}{': ' + detail if detail else ''}"


class InspectionMcpServer:
    """Host the client-facing failure inspection tools in pytest's process."""

    def __init__(
        self,
        *,
        queue: FailureQueue,
        host: str,
        port: int,
        artifact_sink: ArtifactSink | None = None,
        pluginmanager: Any | None = None,
    ) -> None:
        self.queue = queue
        self.host = host
        self.port = port
        self.artifact_sink = artifact_sink
        self.pluginmanager = pluginmanager
        self.endpoint = endpoint_url(host, port)
        self._server: Any = None
        self._thread: threading.Thread | None = None

    def start(self, *, timeout: float = 12.0) -> None:
        try:
            import uvicorn  # noqa: PLC0415  # Import the optional server stack only when selected.
            from mcp.server.fastmcp import FastMCP  # noqa: PLC0415
        except ImportError as error:
            raise DebugMcpDependencyError(
                f"Debug MCP inspection needs pytest-cuke[debug-mcp]: {error}"
            ) from error

        mcp = FastMCP("pytest-cuke-debug-inspection", host=self.host, port=self.port)
        failure_queue = self.queue

        @mcp.tool()
        def inspect_failure() -> dict[str, Any]:
            """Return the active pytest failure and optional BDD execution context."""
            return failure_queue.inspect_failure()

        @mcp.tool()
        def heartbeat(session_id: str, sequence: int) -> dict[str, Any]:
            """Extend the lease for the matching active failure."""
            return failure_queue.heartbeat(session_id=session_id, sequence=sequence)

        @mcp.tool()
        def release_failure(
            session_id: str,
            sequence: int,
            reason: ReleaseReason = "explicit",
        ) -> dict[str, Any]:
            """Release the matching failure, optionally after debugger continuation."""
            return failure_queue.release_failure(
                session_id=session_id,
                sequence=sequence,
                reason=reason,
            )

        if self.artifact_sink is not None:
            artifact_sink = self.artifact_sink
            pluginmanager = self.pluginmanager

            @mcp.tool()
            def submit_artifact(session_id: str, sequence: int, artifact: Any) -> dict[str, Any]:
                """Validate and store paired JSON/Markdown findings for the matching held failure."""
                submitted: dict[str, InvestigationArtifact] = {}

                def write_for_active_failure(active: dict[str, Any]) -> ArtifactWriteResult:
                    validated = InvestigationArtifact.model_validate(artifact)
                    if validated.nodeid != active["nodeid"]:
                        raise _ArtifactFailureMismatch("artifact nodeid does not match the active held failure")
                    if validated.pytest_phase != active["phase"]:
                        raise _ArtifactFailureMismatch("artifact pytest_phase does not match the active held failure")

                    bound = validated.model_copy(update={"bdd_metadata": _bdd_metadata(active.get("bdd_context"))})
                    submitted["artifact"] = bound
                    return artifact_sink.write(
                        sequence=sequence,
                        nodeid=str(active["nodeid"]),
                        payload=bound.model_dump(mode="json"),
                    )

                try:
                    result = failure_queue.write_artifact(
                        session_id=session_id,
                        sequence=sequence,
                        writer=write_for_active_failure,
                    )
                except ValidationError as error:
                    return validation_error_payload(error)
                except _ArtifactFailureMismatch as error:
                    return {"ok": False, "error": "failure_mismatch", "details": [str(error)]}
                except FailureHoldError as error:
                    return {"ok": False, "error": "failure_unavailable", "details": [str(error)]}
                except (OSError, ValueError) as error:
                    return {"ok": False, "error": "filesystem_error", "details": [str(error)]}

                validated_artifact = submitted["artifact"]
                if pluginmanager is not None:
                    pluginmanager.hook.pytest_cuke_debug_mcp_artifact_created(
                        nodeid=validated_artifact.nodeid,
                        pytest_phase=validated_artifact.pytest_phase,
                        bdd_metadata=validated_artifact.bdd_metadata.model_dump(mode="json"),
                        json_path=result.json_path,
                        markdown_path=result.markdown_path,
                        status=validated_artifact.status,
                        summary=validated_artifact.summary,
                    )
                return {"ok": True, **result.as_dict()}

        class _ThreadedUvicornServer(uvicorn.Server):
            def install_signal_handlers(self) -> None:
                return

        app = mcp.streamable_http_app()
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="error", access_log=False)
        server = _ThreadedUvicornServer(config)
        thread = threading.Thread(target=server.run, name="pytest-cuke-debug-mcp-inspection", daemon=True)
        self._server = server
        self._thread = thread
        thread.start()

        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if server.started:
                try:
                    probe_mcp_endpoint(self.endpoint, timeout=min(3.0, max(0.1, deadline - time.monotonic())))
                    return
                except Exception as error:
                    last_error = error
            if not thread.is_alive():
                break
            time.sleep(0.02)
        self.close()
        detail = f": {type(last_error).__name__}: {last_error!r}" if last_error is not None else ""
        raise DebugMcpDependencyError(f"inspection MCP server failed to initialize at {self.endpoint}{detail}")

    def close(self, *, timeout: float = 3.0) -> None:
        server = self._server
        thread = self._thread
        if server is None or thread is None:
            return
        server.should_exit = True
        thread.join(timeout=timeout)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=timeout)
        self._server = None
        self._thread = None


def _bdd_metadata(context: object) -> BddMetadata:
    if not isinstance(context, dict):
        return BddMetadata()
    example_row = context.get("outline_row")
    tags = context.get("tags")
    return BddMetadata(
        feature_path=context.get("feature_path") if isinstance(context.get("feature_path"), str) else None,
        feature_name=context.get("feature_name") if isinstance(context.get("feature_name"), str) else None,
        scenario_name=context.get("scenario_name") if isinstance(context.get("scenario_name"), str) else None,
        step_keyword=context.get("step_keyword") if isinstance(context.get("step_keyword"), str) else None,
        step_text=context.get("step_text") if isinstance(context.get("step_text"), str) else None,
        tags=[tag for tag in tags if isinstance(tag, str)] if isinstance(tags, list) else [],
        example_row=(
            {key: value for key, value in example_row.items() if isinstance(key, str) and isinstance(value, str)}
            if isinstance(example_row, dict)
            else {}
        ),
    )
