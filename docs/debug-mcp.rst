Debug MCP failure inspection
=============================

pytest-cuke can start an optional MCP debugger and hold failed pytest reports
while an external MCP client inspects them. This feature is disabled by
default. Install the optional dependencies before enabling it:

.. code-block:: console

   pip install 'pytest-cuke[debug-mcp]'

Enable it for one run with ``--cuke-mcp-on-fail`` or set
``cuke_mcp_on_fail = true`` in pytest configuration. The default hold timeout
is 30 seconds, the heartbeat lease is 10 seconds, and both servers bind to
``127.0.0.1``. The debugger port is allocated automatically unless a fixed
port is selected.

.. code-block:: console

   pytest --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s

The equivalent pytest settings are ``cuke_mcp_timeout``, ``cuke_mcp_lease``,
``cuke_mcp_host`` and ``cuke_mcp_port``. Durations accept bare seconds or the
``ms``, ``s``, ``m`` and ``h`` suffixes and must be positive finite values.
The debugger port accepts ``auto`` or a fixed value from 1 through 65535.
Command-line values take precedence over pytest configuration.

Binding to a host other than loopback prints a trusted-environment warning.
The optional mcp-pdb server exposes tools that execute Python debugger
commands, so use it only in an environment you trust; see the
`mcp-pdb security note <https://pypi.org/project/mcp-pdb/>`_.

Discovery and endpoints
-----------------------

After both MCP servers complete an initialization handshake, pytest-cuke
atomically publishes the active session at
``.pytest_cache/cuke/debug-mcp/session.json``. Pytest's ``cache_dir`` setting
(for example, ``-o cache_dir=tmp/pytest-cache``) changes the root of this path.
The JSON record includes the session ID, status, host, process IDs, debugger and
inspection URLs, the active failure, and the last release record. Endpoints use
Streamable HTTP at ``/mcp`` and are only advertised after they respond to an MCP
initialize request.

The terminal reports the session ID, both endpoint URLs and discovery path.
While pytest holds a failure, it prints the sequence, phase, node ID and
exception summary.

The debugger endpoint runs the selected mcp-pdb backend in a child process.
The inspection endpoint is a separate in-process MCP server that remains
available while the failed report is held. It exposes these tools:

``inspect_failure()``
   Return the session status and active failure, including optional BDD
   context.

``heartbeat(session_id, sequence)``
   Extend the lease for the currently active failure. A stale session or
   sequence is rejected.

``release_failure(session_id, sequence, reason="explicit")``
   Resume pytest for the matching failure. ``reason`` can be ``explicit`` or
   ``debugger_continuation``. Timeout and lease expiration release the hold
   automatically. Releasing a hold never changes the failed pytest outcome.

Failure and BDD context
-----------------------

Setup, call and teardown failures are published one at a time. The active
failure record contains its sequence number, node ID, phase, exception type
and message. BDD failures also contain feature path/name, scenario name, the
active step keyword/text, combined feature/scenario tags, outline row values
and a breadcrumb with row identity. Plain pytest failures explicitly use a
null ``bdd_context``.

Each hold has a fixed maximum timeout measured from the failure report.
Heartbeats only extend that failure's lease. If no client heartbeats before
the lease expires, or the overall timeout is reached, pytest resumes with the
original failure. Session shutdown closes both servers and records a closed
status with null endpoints in the discovery file.
