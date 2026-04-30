FROM python:3.14-slim

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.rst /app/
COPY src /app/src/
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e '.[test]' pytest-xdist

COPY . /app
RUN install -d -m 700 /root/.ssh \
    && cp /app/tests/e2e/fixtures/remote_xdist/ssh/id_ed25519 /root/.ssh/id_ed25519 \
    && chmod 600 /root/.ssh/id_ed25519 \
    && printf '%s\n' \
        'Host worker1 worker2' \
        '  User root' \
        '  IdentityFile /root/.ssh/id_ed25519' \
        '  StrictHostKeyChecking no' \
        '  UserKnownHostsFile /dev/null' \
        '  LogLevel ERROR' \
        > /root/.ssh/config \
    && chmod 600 /root/.ssh/config

ENTRYPOINT ["python", "tests/e2e/fixtures/remote_xdist/controller_entrypoint.py"]
