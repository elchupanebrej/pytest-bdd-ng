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
``cuke_mcp_host``, ``cuke_mcp_port`` and ``cuke_mcp_artifacts``. Durations accept bare seconds or the
``ms``, ``s``, ``m`` and ``h`` suffixes and must be positive finite values.
The debugger port accepts ``auto`` or a fixed value from 1 through 65535.
Command-line values take precedence over pytest configuration.

Binding to a host other than loopback prints a trusted-environment warning.
Wildcard addresses such as ``0.0.0.0`` and ``::`` are rejected because clients
cannot connect to an advertised wildcard endpoint; choose a specific interface
address that the MCP client can reach.
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

``submit_artifact(session_id, sequence, artifact)``
   Validate and write an investigation for the matching active failure as
   paired UTF-8 JSON and Markdown files. The default directory is
   ``.pytest_cache/cuke/debug-mcp/artifacts/<session-id>``; set
   ``--cuke-mcp-artifacts=DIR`` or ``cuke_mcp_artifacts = DIR`` to choose a
   directory. Relative directories are resolved from pytest's root directory.
   Each filename includes the increasing failure sequence and a
   safe slug of the pytest node ID. The tool returns the artifact ID and both
   paths. Invalid payloads, stale failure identities and filesystem errors
   return structured errors and do not mark the failure as written.

   The ``artifact`` object requires ``artifact_id``, ``nodeid``,
   ``pytest_phase``, ``status``, ``summary``, ``inspected_commands``,
   ``evidence``, ``suspected_cause`` and ``next_action``. Its node ID and phase
   must match the active failure. The phase is ``setup``, ``call`` or
   ``teardown``; status is ``investigated``, ``needs_followup`` or ``resolved``.
   ``links`` is an optional list of strings. Optional ``bdd_metadata`` contains
   ``feature_path``, ``feature_name``, ``scenario_name``, ``step_keyword``,
   ``step_text``, ``tags`` and ``example_row``. Fields with unknown names,
   invalid types, phases or statuses are rejected before files are created.

Artifacts contain the submitted diagnosis fields and BDD metadata from the
active failure context. Content is stored as submitted; pytest-cuke does not
automatically redact it. After files are written, subscribers to
``pytest_cuke_debug_mcp_artifact_created`` receive the node ID, pytest phase,
BDD metadata, both paths, investigation status and summary. Artifact writing
does not require a subscriber.

``release_failure(session_id, sequence, reason="explicit")``
   Resume pytest for the matching failure. ``reason`` can be ``explicit`` or
   ``debugger_continuation``. Continuing with ``c`` or ``continue`` through the
   mcp-pdb ``send_pdb_command`` tool releases the exact active failure captured
   for that debugger command after a short response grace period. Timeout and
   lease expiration release the hold automatically. Releasing a hold never
   changes the failed pytest outcome.

Failure and BDD context
-----------------------

Setup, call and teardown failures are published one at a time. The active
failure record contains its sequence number, node ID, phase, exception type
and message. BDD failures also contain feature path/name, scenario name, the
active step keyword/text, combined feature/scenario tags, outline row values
and a breadcrumb with row identity. Plain pytest failures explicitly use a
null ``bdd_context``.

Each hold has a fixed maximum timeout measured from the failure report. If no
client sends a valid heartbeat, the overall timeout releases the hold. After a
valid heartbeat, the lease is measured from the most recent heartbeat and
expires if the client does not renew it. Whichever deadline releases the hold,
pytest resumes with the original failure. Session shutdown closes both servers
and records a closed status with null endpoints in the discovery file.

pytest-xdist workers
--------------------

With ``pytest-xdist`` installed, Debug MCP supports local ``popen`` workers.
The controller publishes a deterministic worker index at
``.pytest_cache/cuke/debug-mcp/workers.json`` and each worker publishes its
own record under ``.pytest_cache/cuke/debug-mcp/workers/``. The configured
pytest ``cache_dir`` changes both paths. Each worker has its own session ID,
failure sequence, MCP endpoints and release state. Use the session ID and
sequence from the same worker record when calling ``heartbeat`` or
``release_failure``. The root index status is ``holding_failure`` while any
worker is holding a failure; inspect the worker records to select a failure.
If a worker exits unexpectedly, the controller retains its last failure context,
marks it ``worker_crashed`` and clears its debugger and inspection endpoints.

Workers allocate their debugger and inspection ports independently, so leave
the debugger port at its default ``auto`` value when using xdist. A fixed
``--cuke-mcp-port`` is rejected for xdist workers because multiple workers
cannot bind the same debugger port. Remote execnet gateways are unsupported:
workers must be able to publish to the controller's cache directory on a
shared local filesystem. Enabling Debug MCP with a remote gateway reports an
error before starting workers. Run without Debug MCP or use local xdist
workers for this workflow.
