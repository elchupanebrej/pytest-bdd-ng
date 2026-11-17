Feature: Remote xdist grouped execution when a worker dies

  Scenario: Remote unit scenario exits before it settles
    Given a grouped remote scenario that exits its worker in group "unit"
