"""
xdist worker bootstrap for pytest-bdd reporting.

This module is selected via ``pytest_xdist_getremotemodule`` by the live
reporting entrypoint. It must avoid importing ``pytest_bdd`` before
``_prepareconfig()`` runs, otherwise xdist workers can hit
``PytestAssertRewriteWarning`` for already-imported modules.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

from _pytest.config import _prepareconfig  # noqa: PLC2701

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.compatibility.pytest import Stash


class _WorkerInput(TypedDict):
    testrunuid: str
    workerid: str
    workercount: int
    mainargv: list[str]
    pytest_bdd_messages_fragment_worker_id: str
    pytest_bdd_messages_gateway_mode: str
    pytest_bdd_messages_force_publish_failure: bool


class _WorkerOptionDict(TypedDict, total=False):
    basetemp: str | Path | None


class _ReportingChannel(Protocol):
    def receive(self) -> tuple[_WorkerInput, list[str], _WorkerOptionDict, list[str] | None]: ...


class _ParserProtocol(Protocol):
    prog: str


class _PreparedConfig(Protocol):
    _parser: _ParserProtocol
    stash: Stash
    workerinput: _WorkerInput
    workeroutput: dict[str, object]
    hook: _PreparedConfigHook


class _PreparedConfigHook(Protocol):
    def pytest_cmdline_main(self, config: object) -> object: ...


class _ReportingSender(Protocol):
    def sendevent(self, name: str, **kwargs: object) -> None: ...


class _ReportingEventSender(Protocol):
    def __call__(self, name: str, **kwargs: object) -> None: ...


class _XdistRemoteModule(Protocol):
    interactor: _ReportingSender

    def setup_config(self, config: object, basetemp: str | Path | None) -> None: ...


def _build_reporting_worker_environment(workerinput: Mapping[str, object]) -> dict[str, str]:
    env = {
        "PYTEST_XDIST_TESTRUNUID": str(workerinput["testrunuid"]),
        "PYTEST_XDIST_WORKER": str(workerinput["workerid"]),
        "PYTEST_XDIST_WORKER_COUNT": str(workerinput["workercount"]),
        "PYTEST_BDD_XDIST_IS_WORKER": "1",
        "PYTEST_BDD_REPORTING_WORKER_ID": str(
            workerinput.get("pytest_bdd_messages_fragment_worker_id") or workerinput["workerid"],
        ),
    }
    gateway_mode = str(workerinput.get("pytest_bdd_messages_gateway_mode") or "").strip()
    if gateway_mode:
        env["PYTEST_BDD_REPORTING_GATEWAY_MODE"] = gateway_mode
    return env


def _apply_worker_python_path(change_sys_path: list[str] | None) -> None:
    if change_sys_path is None:
        importpath = str(Path.cwd())
        sys.path.insert(0, importpath)
        os.environ["PYTHONPATH"] = importpath + os.pathsep + os.environ.get("PYTHONPATH", "")
    else:
        sys.path = change_sys_path


def _prepare_worker_config(
    workerinput: _WorkerInput,
    args: list[str],
    option_dict: _WorkerOptionDict,
) -> tuple[_PreparedConfig, _XdistRemoteModule]:
    config = _prepareconfig(args, None)
    import xdist.remote as upstream_remote  # noqa: PLC0415

    prepared_config = cast("_PreparedConfig", config)
    typed_remote = cast("_XdistRemoteModule", upstream_remote)
    typed_remote.setup_config(config, option_dict.get("basetemp"))
    prepared_config._parser.prog = Path(workerinput["mainargv"][0]).name  # noqa: SLF001
    prepared_config.workerinput = workerinput
    prepared_config.workeroutput = {}
    return prepared_config, typed_remote


def _build_reporting_sender(
    interactor: _ReportingSender,
    *,
    force_publish_failure: bool,
) -> _ReportingEventSender:
    def reporter_sender(name: str, **kwargs: object) -> None:
        if force_publish_failure:
            msg = "simulated reporter channel failure"
            raise RuntimeError(msg)
        interactor.sendevent(name, **kwargs)

    return reporter_sender


def channel_main(reporting_channel: _ReportingChannel) -> None:
    """Handle channel main."""
    workerinput, args, option_dict, change_sys_path = reporting_channel.receive()

    _apply_worker_python_path(change_sys_path)
    reporting_env = _build_reporting_worker_environment(workerinput)
    os.environ.update(reporting_env)
    gateway_mode = reporting_env.get("PYTEST_BDD_REPORTING_GATEWAY_MODE", "")

    config, upstream_remote = _prepare_worker_config(workerinput, args, option_dict)
    from xdist.remote import WorkerInteractor as XdistWorkerInteractor  # noqa: PLC0415

    from pytest_bdd.model.message_transport import ReportingEventSenderBinding  # noqa: PLC0415

    class ReportingWorkerInteractor(XdistWorkerInteractor):
        def sendevent(self, name: str, **kwargs: object) -> None:
            self.log("sending", name, kwargs)
            self.channel.send((name, kwargs))

    interactor = ReportingWorkerInteractor(config, reporting_channel)
    upstream_remote.interactor = interactor
    force_publish_failure = bool(workerinput.get("pytest_bdd_messages_force_publish_failure"))

    sender = _build_reporting_sender(
        interactor,
        force_publish_failure=force_publish_failure,
    )
    mode = gateway_mode or None
    ReportingEventSenderBinding(
        sender=sender,
        gateway_mode=mode,
    ).set_in_stash(config.stash)
    config.hook.pytest_cmdline_main(config=config)


if __name__ == "__channelexec__":
    channel_main(globals()["channel"])
