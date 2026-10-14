Feature: Debug MCP xdist worker discovery
  An xdist controller advertises each worker's active failure through its own MCP endpoints.

  Scenario: External clients can isolate worker holds and lease expiry
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer has pytest-xdist installed
    And the installed consumer exposes two concurrent xdist debugger failures
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=180s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-mcp-artifacts=xdist-artifacts --cuke-json=report.json --cuke-messages-ndjson=worker-messages.ndjson -n2 --dist=loadfile --maxschedchunk=1 -q"
    And I release the waiting xdist worker after observing one held failure
    Then xdist discovery should record one held worker while its peer waits
    When external MCP clients inspect both advertised xdist worker endpoints, heartbeat, and release them independently
    Then xdist root discovery should show both distinct worker failures
    And heartbeating, releasing, and timing out one worker should leave its peer isolated
    And the written worker artifact should match its failure while the peer release remains missing
    And pytest should report both initial failures and the third follow-up failure, then close every worker service
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=fresh-session-features --cuke-mcp-on-fail --cuke-mcp-timeout=60s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto -n2 --dist=load --maxschedchunk=1 -q"
    And I release the fresh-session workers after observing current discovery
    Then the new xdist session should replace previous worker discovery and pass its probes

  Scenario: Identical worker failures keep separate artifact paths and status
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer has pytest-xdist installed
    And the installed consumer exposes an identical failure on each xdist worker
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=90s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-mcp-artifacts=collision-artifacts -n2 --dist=each -q"
    And an external MCP client submits a structured artifact to each identical worker failure
    Then both workers should retain the same failure identity in distinct sessions
    And pytest should exit with a non-zero code
    And both duplicate worker services should close while preserving the pytest failure
    And identical worker failures should produce separate artifact paths and written release status
