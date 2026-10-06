Feature: Debug MCP xdist worker discovery
  An xdist controller advertises each worker's active failure through its own MCP endpoints.

  Scenario: External clients can isolate worker holds and lease expiry
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has the optional debug MCP extra installed
    And the installed consumer has pytest-xdist installed
    And the installed consumer exposes two concurrent xdist debugger failures
    When I start installed pytest for MCP inspection with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-mcp-on-fail --cuke-mcp-timeout=180s --cuke-mcp-lease=30s --cuke-mcp-host=127.0.0.1 --cuke-mcp-port=auto --cuke-json=report.json -n2 --dist=load --maxschedchunk=1 -q"
    And I release the waiting xdist worker after observing one held failure
    Then xdist discovery should record one held worker while its peer waits
    When external MCP clients inspect both advertised xdist worker endpoints, heartbeat, and release them independently
    Then xdist root discovery should show both distinct worker failures
    And heartbeating, releasing, and timing out one worker should leave its peer isolated
    And pytest should report both initial failures and the third follow-up failure, then close every worker service
