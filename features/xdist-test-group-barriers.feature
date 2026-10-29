Feature: Local xdist test-group completion barriers
  With ordered groups enabled, a later group waits for every selected earlier item to settle
  across local workers. Failed, skipped, and setup-failed items settle the barrier.

  Scenario: A transient state replacement error is retried after a slow write
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = unit
      """
    And consumer file "conftest.py" contains:
      """python
      import os
      import time
      from pathlib import Path
      from types import SimpleNamespace

      from pytest_cuke.test_groups import barrier


      def pytest_configure(config):
          if not hasattr(config, "workerinput"):
              return

          offset = 0
          attempts = 0

          def monotonic():
              return time.monotonic() + offset

          def slow_first_fsync(fd):
              nonlocal offset
              os.fsync(fd)
              if offset == 0:
                  offset = 3

          def transient_replace(source, destination):
              nonlocal attempts
              attempts += 1
              if attempts == 1:
                  raise PermissionError(13, "file is temporarily in use")
              os.replace(source, destination)
              if attempts == 2:
                  Path("replacement-retried").write_text("yes", encoding="utf-8")

          barrier.time = SimpleNamespace(monotonic=monotonic, sleep=time.sleep)
          barrier.os = SimpleNamespace(fsync=slow_first_fsync, replace=transient_replace)
      """
    And consumer file "tests/test_unit.py" contains:
      """python
      from pathlib import Path


      def test_unit_runs_after_state_is_published():
          assert Path("replacement-retried").read_text(encoding="utf-8") == "yes"
      """
    When I run installed pytest with a 60-second watchdog and arguments "-c pytest.ini -n1 --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And pytest output should include "1 passed"

  Scenario: A later group waits for earlier assertion failure, skip, and fixture setup failure
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      cuke_test_group_barrier_timeout = 20
      """
    And consumer file "tests/test_a_unit_failure.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.unit
      def test_unit_assertion_failure(request):
          record_start(request.node.nodeid, "unit")
          signal("unit-failure-started")
          wait_for_signal("unit-skip-started")
          assert False, "expected failure settles the unit group"
      """
    And consumer file "tests/test_b_unit_skip.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.unit
      def test_unit_skip(request):
          record_start(request.node.nodeid, "unit")
          signal("unit-skip-started")
          wait_for_signal("unit-failure-started")
          pytest.skip("expected skip settles the unit group")
      """
    And consumer file "tests/test_c_unit_setup_failure.py" contains:
      """python
      import pytest


      @pytest.fixture
      def failing_resource():
          pytest.fail("expected fixture setup failure settles the unit group")


      @pytest.mark.unit
      def test_unit_setup_failure(failing_resource):
          pytest.fail("the test body must not run")
      """
    And consumer file "tests/test_z_integration_later.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_starts_after_unit_settles(request):
          record_start(request.node.nodeid, "integration")
      """
    When I run installed pytest with a 60-second watchdog and arguments "-c pytest.ini --order-scope=session -n2 --dist=loadfile --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 1
    And consumer terminal outcomes should include failed, skipped, passed
    And every selected "unit" test should settle before any "integration" test starts
    And at least two xdist workers should have recorded group events

  Scenario: A four-worker local run waits for every earlier-group item
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      cuke_test_group_barrier_timeout = 20
      """
    And consumer file "tests/test_a_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_a(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_b_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_b(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_c_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_c(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_d_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_d(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_z_integration.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_waits_for_all_four_unit_files(request):
          record_start(request.node.nodeid, "integration")
      """
    When I run installed pytest with a 60-second watchdog and arguments "-c pytest.ini --order-scope=session -n4 --dist=loadfile --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And every selected "unit" test should settle before any "integration" test starts
    And at least 4 xdist workers should have recorded group events

  Scenario: A deselected middle group cannot block a selected later group
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit contract e2e
      cuke_test_group_default = unit
      """
    And consumer file "tests/test_a_unit.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_selected(request):
          record_start(request.node.nodeid, "unit")
      """
    And consumer file "tests/test_b_contract.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.contract
      def test_contract_deselected(request):
          record_start(request.node.nodeid, "contract")
      """
    And consumer file "tests/test_c_e2e.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.e2e
      def test_e2e_selected(request):
          record_start(request.node.nodeid, "e2e")
      """
    When I run installed pytest with a 45-second watchdog and arguments "-c pytest.ini --order-scope=session -n2 --dist=loadfile -m 'unit or e2e' --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And consumer start events should follow "test_unit_selected,test_e2e_selected"
    And every selected "unit" test should settle before any "e2e" test starts

  Scenario: A configured but empty selection exits without waiting at a barrier
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit contract e2e
      cuke_test_group_default = unit
      """
    And consumer file "tests/test_unit.py" contains:
      """python
      import pytest


      @pytest.mark.unit
      def test_unit_not_selected():
          pytest.fail("no tests should be selected")
      """
    When I run installed pytest with a 30-second watchdog and arguments "-c pytest.ini --order-scope=session -n2 -m contract --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 5
    And the consumer should have no recorded test-group events

  Scenario: Concurrent pytest sessions keep their local group completion state isolated
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      cuke_test_group_barrier_timeout = 20
      """
    And consumer file "tests/test_a_unit_wait.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.unit
      def test_unit_waits_for_its_run_release(request):
          record_start(request.node.nodeid, "unit")
          signal("unit-started")
          wait_for_signal("release-unit", timeout=40)
      """
    And consumer file "tests/test_z_integration.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_starts_after_its_run_release(request):
          record_start(request.node.nodeid, "integration")
      """
    When I run two independent consumer suites through their local xdist group barriers
    Then both independent consumer runs should pass without sharing barrier state

  Scenario: A stalled earlier group reaches its configured timeout with an actionable diagnostic
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      cuke_test_group_barrier_timeout = 1
      """
    And consumer file "tests/test_a_unit_stalled.py" contains:
      """python
      import pytest

      from group_events import record_start, signal, wait_for_signal


      @pytest.mark.unit
      def test_unit_waits_for_external_release(request):
          record_start(request.node.nodeid, "unit")
          signal("unit-stalled")
          wait_for_signal("release-unit", timeout=2)
      """
    And consumer file "tests/test_z_integration_waiting.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_waits_on_unit_barrier(request):
          record_start(request.node.nodeid, "integration")
      """
    When I run installed pytest with a 15-second watchdog and arguments "-c pytest.ini --order-scope=session -n2 --dist=loadfile --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with a non-zero code
    And pytest output should include "timeout"
    And pytest output should include "unit"
    And pytest output should include "integration"
    And pytest output should include "test_integration_waits_on_unit_barrier"
    And pytest output should include "shared filesystem"

  Scenario: Worker interruption fails finitely instead of leaving a later group waiting forever
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the consumer records monotonic test start and terminal events
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      cuke_test_group_barrier_timeout = 2
      """
    And consumer file "tests/test_a_unit_worker_exit.py" contains:
      """python
      import os

      import pytest

      from group_events import record_start


      @pytest.mark.unit
      def test_unit_worker_exits(request):
          record_start(request.node.nodeid, "unit")
          os._exit(17)
      """
    And consumer file "tests/test_z_integration_later.py" contains:
      """python
      import pytest

      from group_events import record_start


      @pytest.mark.integration
      def test_integration_waits_for_interrupted_worker(request):
          record_start(request.node.nodeid, "integration")
      """
    When I run installed pytest with a 30-second watchdog and arguments "-c pytest.ini --order-scope=session -n2 --dist=loadfile --max-worker-restart=0 --cuke-no-autoload -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with a non-zero code
    And pytest output should include "worker"

  Scenario: Invalid local barrier timeout is rejected with a setting-specific diagnostic
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_barrier_timeout = 0
      """
    And consumer file "tests/test_unit.py" contains:
      """python
      import pytest


      @pytest.mark.unit
      def test_unit():
          pass
      """
    When I run installed pytest with a 30-second watchdog and arguments "-c pytest.ini --order-scope=session --cuke-no-autoload --collect-only -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 4
    And pytest output should include "cuke_test_group_barrier_timeout"

  Scenario: Remote xdist workers are rejected before a transport connection is attempted
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit integration
      cuke_test_group_default = integration
      """
    And consumer file "tests/test_unit.py" contains:
      """python
      import pytest


      @pytest.mark.unit
      def test_unit():
          pass
      """
    When I run installed pytest with a 60-second watchdog and arguments "-c pytest.ini --order-scope=session --cuke-no-autoload --dist=load --tx=ssh=invalid.invalid//python=python3 -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 4
    And pytest output should include "shared filesystem"
    And pytest output should not include "bringing up nodes"

  Scenario: Invalid group entries produce deterministic configuration warnings
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "pytest.ini" contains:
      """ini
      [pytest]
      cuke_test_group_order = unit unit integration
      cuke_test_group_default = unknown
      cuke_test_group_paths =
          malformed mapping
          tests/** = missing
      """
    And consumer file "tests/test_unit.py" contains:
      """python
      import pytest


      @pytest.mark.unit
      def test_unit():
          pass
      """
    When I run installed pytest with a 30-second watchdog and arguments "-c pytest.ini --order-scope=session --cuke-no-autoload --collect-only -q"
    Then the installed pytest run should finish before its watchdog
    And pytest should exit with code 0
    And pytest output should include "duplicate"
    And pytest output should include "unknown"
    And pytest output should include "malformed"
