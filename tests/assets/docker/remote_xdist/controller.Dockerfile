FROM python:3.14-slim

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git openssh-client \
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
RUN install -d -m 700 /root/.ssh \
    && cp /app/tests/assets/docker/remote_xdist/ssh/id_ed25519 /root/.ssh/id_ed25519 \
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

ENTRYPOINT ["python", "tests/assets/docker/remote_xdist/controller_entrypoint.py"]
