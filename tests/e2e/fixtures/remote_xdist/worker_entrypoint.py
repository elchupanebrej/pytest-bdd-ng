"""Provide worker entrypoint helpers."""

import os
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path


def main():
    """Run main."""
    remote_mode = os.environ.get("PYTEST_REMOTE_MODE", "socket")

    if remote_mode in {"socket", "via", "proxy"}:
        python_executable = sys.executable
        os.execl(  # noqa: S606
            python_executable,
            python_executable,
            "-m",
            "execnet.script.socketserver",
            "0.0.0.0:8888",
        )
    elif remote_mode == "ssh":
        Path("/run/sshd").mkdir(parents=True, exist_ok=True)
        ssh_dir = Path("/root/.ssh")
        ssh_dir.mkdir(parents=True, exist_ok=True)
        ssh_dir.chmod(0o700)

        pub_key = Path("/etc/pytest-bdd/controller_ed25519.pub")
        if pub_key.exists():
            auth_keys = ssh_dir / "authorized_keys"
            shutil.copy2(pub_key, auth_keys)
            auth_keys.chmod(0o600)

        subprocess.run(["ssh-keygen", "-A"], check=True)  # noqa: S607
        os.execl("/usr/sbin/sshd", "/usr/sbin/sshd", "-D", "-e")  # noqa: S606
    else:
        sys.exit(f"Unsupported PYTEST_REMOTE_MODE: {remote_mode}")


if __name__ == "__main__":
    main()
