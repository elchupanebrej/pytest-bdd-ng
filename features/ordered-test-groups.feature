Feature: Optional ordered pytest test groups
  An installed pytest-cuke consumer can order ordinary pytest test groups without changing
  collection order inside a group, and can keep groups aligned with standard marker selection.

  Scenario: Serial execution uses the configured group order and preserves within-group order
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration e2e
      cuke_test_group_default = integration
      """
    And consumer file "tests/test_a_integration.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_first(request):
          record_start(request.node.nodeid, "integration")
      """
    And consumer file "tests/test_b_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      @pytest.mark.order(2)
      def test_unit_first(request):
          record_start(request.node.nodeid, "unit")


      @pytest.mark.unit
      @pytest.mark.order(1)
      def test_unit_second(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_c_e2e.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.e2e
      def test_e2e_excluded_by_marker_selection(request):
          record_start(request.node.nodeid, "e2e")
      """
    When I run installed pytest with a 45-second watchdog and arguments "-c pytest.ini --order-scope=session -m 'unit or integration' --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And consumer resolved groups should include "test_unit_second=unit,test_unit_first=unit,test_integration_first=integration"
    And consumer collection assignments should include "test_unit_second=unit:item-marker:0,test_unit_first=unit:item-marker:0,test_integration_first=integration:item-marker:1"
    And consumer collection events should follow "test_unit_second,test_unit_first,test_integration_first"
    And consumer start events should follow "test_unit_second,test_unit_first,test_integration_first"
    And pytest output should include "3 passed"

  Scenario: Test markers, last path matches, directory conventions, and defaults resolve in precedence order
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration contract e2e external
      cuke_test_group_default = integration
      cuke_test_group_paths =
          tests/e2e/** = external
          tests/path-late/** = integration
          tests/path-late/** = unit
      markers =
          slow: non-group marker ignored by group resolution
      """
    And consumer file "tests/contract/test_directory_convention.py" contains:
      """python
      from group_events import record_start


      def test_directory_convention(request):
          record_start(request.node.nodeid, "contract")
      """
    And consumer file "tests/e2e/test_direct_marker.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_direct_marker(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/misc/test_default_group.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.slow
      def test_default_group(request):
          record_start(request.node.nodeid, "integration")
      """
    And consumer file "tests/misc/test_highest_marker.py" contains:
      """python
      import pytest

      from group_events import record_start


      pytestmark = [pytest.mark.unit, pytest.mark.e2e]


      def test_highest_marker(request):
          record_start(request.node.nodeid, "e2e")
      """
    And consumer file "tests/path-late/test_last_path_mapping.py" contains:
      """python
      from group_events import record_start


      def test_last_path_mapping(request):
          record_start(request.node.nodeid, "unit")
      """
    When I run installed pytest with a 45-second watchdog and arguments "-c pytest.ini --order-scope=session --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And consumer resolved groups should include "test_direct_marker=unit,test_last_path_mapping=unit,test_default_group=integration,test_directory_convention=contract,test_highest_marker=e2e"
    And consumer collection assignments should include "test_direct_marker=unit:item-marker:0,test_last_path_mapping=unit:path-mapping:0,test_default_group=integration:default:1,test_directory_convention=contract:directory:2,test_highest_marker=e2e:conftest-marker:3"
    And consumer collection events should follow "test_direct_marker,test_last_path_mapping,test_default_group,test_directory_convention,test_highest_marker"
    And consumer start events should follow "test_direct_marker,test_last_path_mapping,test_default_group,test_directory_convention,test_highest_marker"

  Scenario: A group marker inherited from a directory conftest affects real pytest ordering
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      """
    And consumer file "tests/conftest.py" contains:
      """python
      import pytest


      def pytest_itemcollected(item):
          if item.path.name == "test_z_conftest_group.py":
              item.parent.add_marker(pytest.mark.unit)
      """
    And consumer file "tests/test_a_integration.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration(request):
          record_start(request.node.nodeid, "integration")
      """
    And consumer file "tests/test_z_conftest_group.py" contains:
      """python
      from group_events import record_start


      def test_inherited_from_conftest(request):
          record_start(request.node.nodeid, "unit")
      """
    When I run installed pytest with a 45-second watchdog and arguments "-c pytest.ini --order-scope=session --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And consumer start events should follow "test_inherited_from_conftest,test_integration"

  Scenario: An empty configured group order keeps the default workflow ungrouped
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      markers =
          unit: selectable test group
          integration: selectable test group
      """
    And consumer file "tests/test_a_integration.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.integration
      def test_integration_first(request):
          record_start(request.node.nodeid, "integration")
          signal("integration-started")
          wait_for_signal("unit-started")
          signal("integration-observed-unit")
      """
    And consumer file "tests/test_b_unit.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.unit
      def test_unit_second(request):
          record_start(request.node.nodeid, "unit")
          signal("unit-started")
          wait_for_signal("integration-started")
          wait_for_signal("integration-observed-unit")
      """
    When I run installed pytest with a 45-second watchdog and arguments "-n2 --dist=loadfile -m 'unit or integration' --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And at least two xdist workers should have recorded group events
    And the consumer should have no test-group barrier state root
