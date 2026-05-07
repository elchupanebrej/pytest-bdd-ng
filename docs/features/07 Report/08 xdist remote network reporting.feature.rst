Feature: xdist remote network reporting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents that pytest-bdd-ng produces one consolidated
NDJSON report when test workers communicate with the controller over
real network transports: execnet socket, relay (chained proxy), and SSH.

Each scenario uses Docker containers with independent filesystems — no
shared volume between the controller and worker — intentionally testing
that the xdist/execnet channel is the sole reporting transport. The same
boundary also centralizes live formatter ownership on the
controller/main authority so worker processes never render competing
formatter output. No manual ``-s`` or ``--capture=no`` override is
required when the controller requests a terminal formatter, and
formatter discovery continues to come from the canonical pytest plugin
inventory rather than package scanning.

Scenario: Consolidated report is produced when workers communicate over execnet socket
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Docker is available

- When run pytest across xdist workers over socket gateway

- Then the distributed run succeeds and a consolidated NDJSON report is
  produced

--------------

Scenario: Consolidated report is produced when workers communicate via a relay node
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Docker is available

- When run pytest across xdist workers over relay gateway

- Then the distributed run succeeds and a consolidated NDJSON report is
  produced

--------------

Scenario: Consolidated report is produced when workers communicate over SSH
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Docker is available

- When run pytest across xdist workers over ssh gateway

- Then the distributed run succeeds and a consolidated NDJSON report is
  produced
