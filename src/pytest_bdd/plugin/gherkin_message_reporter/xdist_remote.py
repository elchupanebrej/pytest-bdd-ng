from __future__ import annotations

import os
import sys
from pathlib import Path

from _pytest.config import _prepareconfig

if __name__ == "__channelexec__":
    channel = channel  # type: ignore[name-defined]  # noqa: F821
    workerinput, args, option_dict, change_sys_path = channel.receive()  # type: ignore[name-defined]

    if change_sys_path is None:
        importpath = str(Path.cwd())
        sys.path.insert(0, importpath)
        os.environ["PYTHONPATH"] = importpath + os.pathsep + os.environ.get("PYTHONPATH", "")
    else:
        sys.path = change_sys_path

    os.environ["PYTEST_XDIST_TESTRUNUID"] = workerinput["testrunuid"]
    os.environ["PYTEST_XDIST_WORKER"] = workerinput["workerid"]
    os.environ["PYTEST_XDIST_WORKER_COUNT"] = str(workerinput["workercount"])

    config = _prepareconfig(args, None)
    import xdist.remote as upstream_remote

    from pytest_bdd.model.message_transport import install_reporting_event_sender

    class ReportingWorkerInteractor(upstream_remote.WorkerInteractor):
        def sendevent(self, name: str, **kwargs: object) -> None:
            self.log("sending", name, kwargs)
            self.channel.send((name, kwargs))

    upstream_remote.setup_config(config, option_dict.get("basetemp"))
    config._parser.prog = Path(workerinput["mainargv"][0]).name
    config.workerinput = workerinput  # type: ignore[attr-defined]
    config.workeroutput = {}  # type: ignore[attr-defined]

    interactor = ReportingWorkerInteractor(config, channel)
    upstream_remote.interactor = interactor
    force_publish_failure = bool(workerinput.get("pytest_bdd_messages_force_publish_failure"))

    def reporter_sender(name: str, **kwargs: object) -> None:
        if force_publish_failure:
            msg = "simulated reporter channel failure"
            raise RuntimeError(msg)
        interactor.sendevent(name, **kwargs)

    install_reporting_event_sender(
        config,
        reporter_sender,
        gateway_mode=str(workerinput.get("pytest_bdd_messages_gateway_mode") or "").strip() or None,
    )
    config.hook.pytest_cmdline_main(config=config)
