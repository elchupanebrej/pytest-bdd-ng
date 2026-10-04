Feature: Debug MCP failure inspection
  An installed consumer can leave ordinary failures alone by default and opt in to a
  real MCP inspection session that retains BDD context until an external client releases it.

  Scenario: MCP stays inert when failure inspection is not selected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes a debugger failure BDD probe
    And the consumer has a startup guard for MCP imports and child processes
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "debug MCP failure sentinel"
    And the consumer should report no MCP backend import or child process
    And consumer artifact "report.json" should retain the failed debugger BDD scenario

  Scenario: An external MCP SDK client inspects and releases a failed BDD step
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer exposes a debugger failure BDD probe
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=30s --cuke-mcp-lease=10s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    And an external MCP client inspects the advertised failure, heartbeats, and releases it
    Then pytest should exit with a non-zero code
    And the MCP client observation should confirm the advertised endpoint and BDD failure context
    And the MCP discovery record should no longer advertise a live endpoint
    And consumer artifact "report.json" should retain the failed debugger BDD scenario
    And consumer artifact "messages.ndjson" should retain the debugger failure evidence
