FROM python:3.14-slim

ENV PYTEST_CUKE_BUILD_GO=off
WORKDIR /workspace

RUN apt-get update \
    && apt-get install --yes --no-install-recommends openssh-client openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 755 /run/sshd /artifacts

COPY pyproject.toml setup.cfg setup.py README.rst LICENSE.rst ./
COPY src/pytest_cuke ./src/pytest_cuke
COPY tests/external/remote-xdist ./tests/external/remote-xdist

RUN python -m pip install --no-cache-dir -e '.[test]' 'pytest-xdist>=3.8,<4'

CMD ["sleep", "infinity"]
