Feature: Debug MCP failure inspection
  An installed consumer can leave ordinary failures alone by default and opt in to a
  real MCP inspection session that retains BDD context until an external client releases it.

  Scenario: MCP stays inert when failure inspection is not selected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes a debugger failure BDD probe
    And the installed consumer exposes an ordinary passing pytest test
    And the consumer has a startup guard for MCP imports and child processes
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "debug MCP failure sentinel"
    And consumer marker file "ordinary-run.marker" should contain lines "passed"
    And the consumer should report no MCP backend import or child process
    And consumer artifact "report.json" should retain the failed debugger BDD scenario

  Scenario: Installed pytest help describes Debug MCP controls and defaults
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--help"
    Then installed pytest help should describe the Debug MCP options and defaults

  Scenario: Invalid Debug MCP duration fails before backend startup
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has a startup guard for MCP imports and child processes
    When I run installed pytest with arguments "--cuke-mcp-on-fail --cuke-mcp-timeout=invalid"
    Then pytest should exit with code 4
    And pytest output should include "invalid parse_duration value: 'invalid'"
    And the consumer should report no MCP backend import or child process

  Scenario: Invalid Debug MCP port fails before backend startup
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has a startup guard for MCP imports and child processes
    When I run installed pytest with arguments "--cuke-mcp-on-fail --cuke-mcp-port=70000"
    Then pytest should exit with code 4
    And pytest output should include "invalid parse_port value: '70000'"
    And the consumer should report no MCP backend import or child process

  Scenario: A plain pytest call failure is held with explicit null BDD context
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client inspects and releases the held plain pytest failure
    Then pytest should exit with a non-zero code
    And the plain pytest MCP observation should show a "call" failure with null BDD context
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario Outline: Setup and teardown failures remain held for external inspection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest failure during "<phase>"
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client inspects and releases the held plain pytest failure
    Then pytest should exit with a non-zero code
    And the plain pytest MCP observation should show a "<phase>" failure with null BDD context
    And the MCP discovery record should no longer advertise a live endpoint

    Examples:
      | phase   |
      | setup   |
      | teardown |

  Scenario: A held failure releases on its overall timeout without an MCP client
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a delayed plain pytest failure
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=3s --cuke-mcp-lease=500ms --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And no external MCP client connects before the held failure times out
    Then pytest should exit with a non-zero code
    And the MCP timeout observation should prove release from the current hold with reason "timeout"
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: A single external heartbeat holds the failure only until its lease expires
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=2s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client heartbeats once and stops renewing the lease
    Then pytest should exit with a non-zero code
    And the MCP lease observation should prove bounded release from the current hold with reason "lease_expired"
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: An external release after explicit release returns a controlled error
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    And the installed consumer has a trailing pytest test that waits after release
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client releases the held failure and retries release
    Then pytest should exit with a non-zero code
    And the MCP repeated-release observation should report the controlled unavailable-failure error
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: Cancelling pytest closes the held failure and debugger child
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a debugger failure BDD probe
    And installed pytest starts in an isolated signal process group
    And the consumer has a startup guard for MCP imports and child processes
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And the harness interrupts only the active pytest consumer process
    Then the interrupted pytest process should finish with failure and close its debugger child
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: Selecting Debug MCP without its optional extra starts no endpoint or child
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has no optional Debug MCP dependencies
    And the installed consumer exposes a plain pytest call failure
    And the consumer has a startup guard for MCP imports and child processes
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail -q"
    Then the selected MCP launch should fail before advertising an endpoint or keeping a child alive

  Scenario: An occupied fixed debugger port leaves no advertised endpoint or live child
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    And the consumer has a startup guard for MCP imports and child processes
    And the consumer holds an available loopback port open
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-host=127.0.0.1 --cuke-mcp-port={mcp_occupied_port} -q"
    Then the selected MCP launch should fail before advertising an endpoint or keeping a child alive

  Scenario: Stale client operations cannot affect the next held failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes two ordered debugger failures
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client submits stale session and sequence operations while the next failure is held
    Then pytest should exit with a non-zero code
    And the MCP stale-operation observation should show client errors and preserve the next failure
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: An external MCP SDK client inspects and releases a failed BDD step
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_mcp_on_fail = false
      cuke_mcp_timeout = "1s"
      cuke_mcp_lease = "1s"
      """
    And the installed consumer exposes a debugger failure BDD probe
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    And an external MCP client inspects the advertised failure, heartbeats, and releases it
    Then pytest should exit with a non-zero code
    And the MCP client observation should confirm the advertised endpoint and BDD failure context
    And pytest output should announce the Debug MCP session, endpoints, and held failure
    And the MCP discovery record should no longer advertise a live endpoint
    And consumer artifact "report.json" should retain the failed debugger BDD scenario
    And consumer artifact "messages.ndjson" should retain the debugger failure evidence

  Scenario: A non-loopback MCP bind emits the trust warning
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    And the consumer has a bindable non-loopback address for MCP
    When I run installed pytest with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-host={mcp_nonlocal_host} --cuke-mcp-port=auto --cuke-mcp-timeout=1s -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "WARNING: Debug MCP is bound to a non-local host"

  Scenario: An external MCP client validates and submits a structured investigation artifact
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a debugger failure BDD probe
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-mcp-artifacts=artifact-output --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    And an external MCP client rejects mismatched artifacts and submits an investigation artifact under "artifact-output"
    Then pytest should exit with a non-zero code
    And the MCP artifact observation should confirm strict validation, failure binding, BDD metadata, and written release status
    And the consumer MCP artifact files should contain the submitted JSON and Markdown pair under "artifact-output"
    And the consumer artifact hook should report the active BDD failure and saved paths under "artifact-output"
    And the MCP discovery record should no longer advertise a live endpoint
    And consumer artifact "report.json" should retain the failed debugger BDD scenario
    And consumer artifact "messages.ndjson" should retain the debugger failure evidence

  Scenario: Configured artifact directory is used without a CLI override
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_mcp_artifacts = "configured-artifacts"
      """
    And the installed consumer exposes a debugger failure BDD probe
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    And an external MCP client rejects mismatched artifacts and submits an investigation artifact under "configured-artifacts"
    Then pytest should exit with a non-zero code
    And the MCP artifact observation should confirm strict validation, failure binding, BDD metadata, and written release status
    And the consumer MCP artifact files should contain the submitted JSON and Markdown pair under "configured-artifacts"
    And the consumer artifact hook should report the active BDD failure and saved paths under "configured-artifacts"
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: An external MCP client can submit an artifact for a plain pytest failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a plain pytest call failure
    And the installed consumer records Debug MCP artifact hook calls
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-mcp-artifacts=plain-artifacts -q"
    And an external MCP client submits an artifact for the held plain pytest failure under "plain-artifacts"
    Then pytest should exit with a non-zero code
    And the plain failure artifact observation should confirm null BDD context, default metadata, and written release status
    And the consumer MCP artifact files should contain the submitted JSON and Markdown pair under "plain-artifacts"
    And the consumer artifact hook should report the active BDD failure and saved paths under "plain-artifacts"
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: A released failure sequence cannot attach an artifact to the next held failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes two ordered debugger failures
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -q"
    And an external MCP client tries the first failure sequence after the next failure is held
    Then pytest should exit with a non-zero code
    And the MCP artifact client observation should show the stale sequence did not affect the next failure
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: Filesystem errors leave the held failure available for release
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a debugger failure BDD probe
    And the installed consumer has a file blocking its configured artifact directory
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-mcp-artifacts=occupied-root/child --cuke-json=report.json -q"
    And an external MCP client submits an artifact and releases the held failure after the write fails
    Then pytest should exit with a non-zero code
    And the MCP filesystem error observation should show the failure remained held until release
    And consumer artifact "report.json" should retain the failed debugger BDD scenario
    And the MCP discovery record should no longer advertise a live endpoint

  Scenario: Continuing the advertised debugger session releases the exact held failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a debugger failure BDD probe
    And the installed consumer has a small mcp-pdb debug target
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=90s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    And an external MCP client continues a session through the advertised debugger endpoint
    Then pytest should exit with a non-zero code
    And debugger continuation should release the exact advertised failure
    And the MCP discovery record should no longer advertise a live endpoint
    And consumer artifact "report.json" should retain the failed debugger BDD scenario
    And consumer artifact "messages.ndjson" should retain the debugger failure evidence
