Feature: remote Debug MCP failure hold

  @remote-debug
  Scenario: A remote worker holds its failure for inspection
    Given a remote debug failure that waits for inspection
