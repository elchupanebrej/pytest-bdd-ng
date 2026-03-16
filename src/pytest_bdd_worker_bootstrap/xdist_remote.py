"""xdist worker bootstrap for pytest-bdd reporting.

This module is selected via ``pytest_xdist_getremotemodule`` by the live
reporting entrypoint. It must avoid importing ``pytest_bdd`` before
``_prepareconfig()`` runs, otherwise xdist workers can hit
``PytestAssertRewriteWarning`` for already-imported modules.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from _pytest.config import _prepareconfig

if TYPE_CHECKING:
    from collections.abc import Mapping


def _build_reporting_worker_environment(workerinput: Mapping[str, object]) -> dict[str, str]:
    env = {
        "PYTEST_XDIST_TESTRUNUID": str(workerinput["testrunuid"]),
        "PYTEST_XDIST_WORKER": str(workerinput["workerid"]),
        "PYTEST_XDIST_WORKER_COUNT": str(workerinput["workercount"]),
        "PYTEST_BDD_XDIST_IS_WORKER": "1",
        "PYTEST_BDD_REPORTING_WORKER_ID": str(
            workerinput.get("pytest_bdd_messages_fragment_worker_id") or workerinput["workerid"]
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


def _prepare_worker_config(workerinput: Mapping[str, object], args: list[str], option_dict: Mapping[str, object]):
    config = _prepareconfig(args, None)
    import xdist.remote as upstream_remote

    upstream_remote.setup_config(config, option_dict.get("basetemp"))
    config._parser.prog = Path(workerinput["mainargv"][0]).name
    config.workerinput = workerinput  # type: ignore[attr-defined]
    config.workeroutput = {}  # type: ignore[attr-defined]
    return config, upstream_remote


def _build_reporting_sender(
    interactor,
    *,
    force_publish_failure: bool,
):
    def reporter_sender(name: str, **kwargs: object) -> None:
        if force_publish_failure:
            msg = "simulated reporter channel failure"
            raise RuntimeError(msg)
        interactor.sendevent(name, **kwargs)

    return reporter_sender


def channel_main(reporting_channel: Any) -> None:
    workerinput, args, option_dict, change_sys_path = reporting_channel.receive()

    _apply_worker_python_path(change_sys_path)
    reporting_env = _build_reporting_worker_environment(workerinput)
    os.environ.update(reporting_env)
    gateway_mode = reporting_env.get("PYTEST_BDD_REPORTING_GATEWAY_MODE", "")

    config, upstream_remote = _prepare_worker_config(workerinput, args, option_dict)

    from pytest_bdd.model.message_transport import install_reporting_event_sender

    class ReportingWorkerInteractor(upstream_remote.WorkerInteractor):
        def sendevent(self, name: str, **kwargs: object) -> None:
            self.log("sending", name, kwargs)
            self.channel.send((name, kwargs))

    interactor = ReportingWorkerInteractor(config, reporting_channel)
    upstream_remote.interactor = interactor
    force_publish_failure = bool(workerinput.get("pytest_bdd_messages_force_publish_failure"))

    install_reporting_event_sender(
        config,
        _build_reporting_sender(
            interactor,
            force_publish_failure=force_publish_failure,
        ),
        gateway_mode=gateway_mode or None,
    )
    config.hook.pytest_cmdline_main(config=config)


if __name__ == "__channelexec__":
    channel_main(globals()["channel"])
