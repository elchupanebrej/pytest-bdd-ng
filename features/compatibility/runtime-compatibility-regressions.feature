@e2e
Feature: Runtime compatibility regressions
  Worker-specific paths and runtime-specific frame locals keep pytest-cuke usable.

  Scenario: xdist execnet worker roots produce stable scenario node IDs
    Given worker-root pytester projects share one checkout feature
    When I collect the checkout feature from both worker roots
    Then both child collections expose the same worker-independent scenario node ID

  Scenario: step registration accepts FrameLocalsProxy-style locals
    When I register a target fixture in FrameLocalsProxy-style locals
    Then registration adds a fixture without requiring mapping.setdefault
