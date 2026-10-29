"""Start an execnet or SSH service used by the remote xdist carrier."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _start_ssh_daemon() -> None:
    key_path = Path("/run/remote-ssh/id_ed25519.pub")
    if not key_path.is_file():
        raise SystemExit(
            "remote xdist SSH worker has no controller public key; run the SSH carrier so it can create an ephemeral key"
        )

    ssh_dir = Path("/root/.ssh")
    ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    ssh_dir.chmod(0o700)
    shutil.copyfile(key_path, ssh_dir / "authorized_keys")
    (ssh_dir / "authorized_keys").chmod(0o600)

    sshd_config = Path("/etc/ssh/sshd_config.d/remote-xdist.conf")
    sshd_config.write_text(
        "PermitRootLogin yes\n"
        "PasswordAuthentication no\n"
        "PubkeyAuthentication yes\n"
        "AuthorizedKeysFile .ssh/authorized_keys\n"
        "UsePAM no\n",
        encoding="utf-8",
    )
    subprocess.run(["ssh-keygen", "-A"], check=True)
    os.execv("/usr/sbin/sshd", ["/usr/sbin/sshd", "-D", "-e"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", action="store_true")
    args = parser.parse_args()

    mode = os.environ.get("REMOTE_XDIST_MODE", "")
    if not args.proxy and mode == "ssh":
        _start_ssh_daemon()
        return 0

    os.execv(
        sys.executable,
        [sys.executable, "-m", "execnet.script.socketserver", "0.0.0.0:8888"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
