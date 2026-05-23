FROM python:3.14-slim

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git openssh-server \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.rst /app/
COPY src /app/src/
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e '.[test]' pytest-xdist

COPY tests/__init__.py /app/tests/
COPY tests/conftest.py /app/tests/
COPY tests/assets /app/tests/assets/
COPY tests/cases/contract /app/tests/cases/contract/

RUN install -d -m 700 /root/.ssh /etc/pytest-bdd /etc/ssh/sshd_config.d /run/sshd \
    && cp /app/tests/assets/docker/remote_xdist/ssh/id_ed25519.pub /etc/pytest-bdd/controller_ed25519.pub \
    && chmod 644 /etc/pytest-bdd/controller_ed25519.pub \
    && printf '%s\n' \
        'PermitRootLogin yes' \
        'PasswordAuthentication no' \
        'PubkeyAuthentication yes' \
        'AuthorizedKeysFile .ssh/authorized_keys' \
        'UsePAM no' \
        > /etc/ssh/sshd_config.d/pytest-bdd.conf \
    && ssh-keygen -A

ENTRYPOINT ["python", "tests/assets/docker/remote_xdist/worker_entrypoint.py"]
