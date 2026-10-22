Feature: Local and subprocess Cucumber Messages consolidation
  An installed consumer running local xdist workers receives one complete,
  deterministic Messages stream with valid worker identities and references.
  The separate explicit popen-gateway scenario exercises subprocess report transport;
  a test-managed localhost socket gateway exercises execnet socket transport with
  xdist rsync staging; neither local transport scenario claims cross-host SSH parity.

  Scenario: Two local workers consolidate one scenario and every outline row
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      import threading
      import time
      import uuid
      from pathlib import Path
      import pytest

      from pytest_cuke import given, parsers

      _consumer_config = None
      _observation_lock = threading.Lock()


      def pytest_configure(config):
          global _consumer_config
          _consumer_config = config


      @given(parsers.parse("worker case {case} completes"))
      def worker_case_completes(case, pytestconfig):
          worker_id = os.environ.get("PYTEST_XDIST_WORKER")
          assert worker_id, "the local xdist contract must run each case on a worker"
          messages_path = pytestconfig.getoption("cuke_messages_ndjson")
          observations = Path(f"{messages_path}.worker-observations")
          observations.mkdir(parents=True, exist_ok=True)
          observation = observations / f"{case}-{uuid.uuid4().hex}.json"
          temporary_observation = observation.with_suffix(".json.tmp")
          temporary_observation.write_text(
              json.dumps({"case": case, "worker_id": worker_id}), encoding="utf-8"
          )
          temporary_observation.replace(observation)

          deadline = time.monotonic() + 20
          while time.monotonic() < deadline:
              observed_workers = {
                  json.loads(path.read_text(encoding="utf-8"))["worker_id"]
                  for path in observations.glob("*.json")
              }
              if len(observed_workers) >= 2:
                  return
              time.sleep(0.01)
          raise AssertionError("the installed pytest run did not execute cases on two xdist workers")


      def pytest_cuke_message_batch(config, batch):
          messages_path = config.getoption("cuke_messages_ndjson")
          live_batches = Path(f"{messages_path}.live-batches.jsonl")
          with _observation_lock:
              with live_batches.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(batch, sort_keys=True) + "\n")


      @pytest.hookimpl(trylast=True)
      def pytest_testnodedown(node, error):
          worker_id = getattr(getattr(node, "gateway", None), "id", "unknown")
          worker_output = getattr(node, "workeroutput", {})
          record = {
              "worker_id": worker_id,
              "error": str(error) if error is not None else None,
              "exitstatus": worker_output.get("exitstatus"),
              "worker_output_keys": sorted(worker_output),
              "transport": worker_output.get("pytest_cuke_message_transport"),
          }
          messages_path = _consumer_config.getoption("cuke_messages_ndjson")
          manifests = Path(f"{messages_path}.worker-manifests.jsonl")
          with _observation_lock:
              with manifests.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(record, sort_keys=True) + "\n")
      """
    And consumer file "features/worker-cases.feature" contains:
      """gherkin
      Feature: Distributed worker cases
        Scenario: Standalone worker case completes
          Given worker case standalone completes

        Scenario Outline: Outline worker case <case> completes
          Given worker case <case> completes

        Examples:
          | case  |
          | alpha |
          | beta  |
          | alpha |
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=first.ndjson -n2 --dist=load --color=no -q"
    Then the test outcome should have 4 passed scenarios
    And consumer artifact "first.ndjson.worker-manifests.jsonl" should report complete manifests matching "first.ndjson.live-batches.jsonl"
    And consumer artifact "first.ndjson" should be one complete local xdist Messages stream for the four selected rows
    And consumer artifact "first.ndjson.live-batches.jsonl" should contain incomplete live worker batches
    And pytest should exit with code 0
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=second.ndjson -n2 --dist=load --color=no -q"
    Then the test outcome should have 4 passed scenarios
    And consumer artifact "second.ndjson.worker-manifests.jsonl" should report complete manifests matching "second.ndjson.live-batches.jsonl"
    And consumer artifact "second.ndjson" should be one complete local xdist Messages stream for the four selected rows
    And consumer artifact "second.ndjson.live-batches.jsonl" should contain incomplete live worker batches
    And pytest should exit with code 0
    And consumer artifacts "first.ndjson" and "second.ndjson" should have identical normalized local xdist output
    And the installed consumer should have no leftover local Messages worker fragments

  Scenario: Two explicit popen gateways transfer Messages through reports without worker-shared files
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      import threading
      from pathlib import Path

      import pytest
      from pytest_cuke import given, parsers

      _consumer_config = None
      _observation_lock = threading.Lock()


      def pytest_configure(config):
          global _consumer_config
          _consumer_config = config


      @given(parsers.parse("worker case {case} completes"))
      def worker_case_completes(case):
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the subprocess gateway must execute the case in a worker"


      def pytest_cuke_message_batch(config, batch):
          messages_path = config.getoption("cuke_messages_ndjson")
          live_batches = Path(f"{messages_path}.live-batches.jsonl")
          with _observation_lock:
              with live_batches.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(batch, sort_keys=True) + "\n")


      @pytest.hookimpl(trylast=True)
      def pytest_testnodedown(node, error):
          worker_id = getattr(getattr(node, "gateway", None), "id", "unknown")
          worker_output = getattr(node, "workeroutput", {})
          record = {
              "worker_id": worker_id,
              "error": str(error) if error is not None else None,
              "exitstatus": worker_output.get("exitstatus"),
              "worker_output_keys": sorted(worker_output),
              "transport": worker_output.get("pytest_cuke_message_transport"),
          }
          messages_path = _consumer_config.getoption("cuke_messages_ndjson")
          manifests = Path(f"{messages_path}.worker-manifests.jsonl")
          with _observation_lock:
              with manifests.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(record, sort_keys=True) + "\n")
      """
    And consumer file "features/subprocess-worker-cases.feature" contains:
      """gherkin
      Feature: Subprocess gateway cases
        Scenario: Standalone worker case completes
          Given worker case standalone completes

        Scenario Outline: Outline worker case <case> completes
          Given worker case <case> completes

          Examples:
            | case  |
            | alpha |
            | beta  |
            | alpha |
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=subprocess.ndjson --dist=load --tx=2*popen --color=no -q"
    Then the test outcome should have 4 passed scenarios
    And consumer artifact "subprocess.ndjson.worker-manifests.jsonl" should report complete manifests matching "subprocess.ndjson.live-batches.jsonl"
    And consumer artifact "subprocess.ndjson" should be one complete subprocess gateway Messages stream for the four selected rows
    And consumer artifact "subprocess.ndjson.live-batches.jsonl" should contain incomplete live worker batches
    And pytest should exit with code 0
    And the installed consumer should have no leftover local Messages worker fragments

  Scenario: Local xdist consolidates passing failing and skipped cases
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import threading
      from pathlib import Path

      import pytest
      from pytest_cuke import given, parsers

      _consumer_config = None
      _observation_lock = threading.Lock()


      def pytest_configure(config):
          global _consumer_config
          _consumer_config = config


      @given(parsers.parse("mixed worker case {case} completes"))
      def mixed_worker_case_completes(case):
          if case == "failed":
              pytest.fail("expected worker case failure")
          if case == "skipped":
              pytest.skip("expected worker case skip")


      def pytest_cuke_message_batch(config, batch):
          messages_path = config.getoption("cuke_messages_ndjson")
          live_batches = Path(f"{messages_path}.live-batches.jsonl")
          with _observation_lock:
              with live_batches.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(batch, sort_keys=True) + "\n")


      @pytest.hookimpl(trylast=True)
      def pytest_testnodedown(node, error):
          worker_id = getattr(getattr(node, "gateway", None), "id", "unknown")
          worker_output = getattr(node, "workeroutput", {})
          record = {
              "worker_id": worker_id,
              "error": str(error) if error is not None else None,
              "exitstatus": worker_output.get("exitstatus"),
              "worker_output_keys": sorted(worker_output),
              "transport": worker_output.get("pytest_cuke_message_transport"),
          }
          messages_path = _consumer_config.getoption("cuke_messages_ndjson")
          manifests = Path(f"{messages_path}.worker-manifests.jsonl")
          with _observation_lock:
              with manifests.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(record, sort_keys=True) + "\n")
      """
    And consumer file "features/mixed-worker-cases.feature" contains:
      """gherkin
      Feature: Mixed worker outcomes
        Scenario Outline: Worker case <case> completes
          Given mixed worker case <case> completes

        Examples:
          | case    |
          | passed  |
          | failed  |
          | skipped |
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=mixed.ndjson -n2 --dist=load --max-worker-restart=0 --color=no -q"
    Then pytest output should report one passed, one failed, and one skipped test
    And consumer artifact "mixed.ndjson" should contain the complete mixed local xdist Messages stream
    And consumer artifact "mixed.ndjson.worker-manifests.jsonl" should report complete manifests matching "mixed.ndjson.live-batches.jsonl" despite the expected test failure
    And pytest should exit with code 1
    And the installed consumer should have no leftover local Messages worker fragments

  Scenario: Local xdist reports a crashed worker and flushes the partial Messages stream
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      import threading
      from pathlib import Path

      import pytest
      from pytest_cuke import given, parsers

      _consumer_config = None
      _observation_lock = threading.Lock()


      def pytest_configure(config):
          global _consumer_config
          _consumer_config = config


      @given(parsers.parse("crash probe case {case} runs"))
      def crash_probe_case_runs(case):
          if case == "crash":
              os._exit(23)
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the survivor must run in an xdist worker"


      def pytest_cuke_message_batch(config, batch):
          messages_path = config.getoption("cuke_messages_ndjson")
          live_batches = Path(f"{messages_path}.live-batches.jsonl")
          with _observation_lock:
              with live_batches.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(batch, sort_keys=True) + "\n")


      @pytest.hookimpl(trylast=True)
      def pytest_testnodedown(node, error):
          worker_id = getattr(getattr(node, "gateway", None), "id", "unknown")
          worker_output = getattr(node, "workeroutput", {})
          record = {
              "worker_id": worker_id,
              "error": str(error) if error is not None else None,
              "exitstatus": worker_output.get("exitstatus"),
              "worker_output_keys": sorted(worker_output),
              "transport": worker_output.get("pytest_cuke_message_transport"),
          }
          messages_path = _consumer_config.getoption("cuke_messages_ndjson")
          manifests = Path(f"{messages_path}.worker-manifests.jsonl")
          with _observation_lock:
              with manifests.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(record, sort_keys=True) + "\n")
      """
    And consumer file "features/crash-worker-cases.feature" contains:
      """gherkin
      Feature: Crashed worker cases
        Scenario: Crashed worker exits abruptly
          Given crash probe case crash runs

        Scenario: Remaining worker sends messages
          Given crash probe case survive runs
      """
    When I run installed pytest with a 45-second watchdog and arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=crash.ndjson -n2 --dist=load --max-worker-restart=0 --color=no -q"
    Then pytest output should report the crashed xdist worker and partial Messages diagnostics
    And consumer artifact "crash.ndjson" should contain the flushed partial local xdist Messages stream
    And consumer artifact "crash.ndjson.worker-manifests.jsonl" should record the crashed worker
    And pytest should exit with a non-zero code

  Scenario: A crashed worker in terminal formatter mode leaves no temporary Messages file
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer temporary directory "worker-messages-tmp" is configured as TMPDIR
    And consumer file "conftest.py" contains:
      """python
      import os
      import sys
      from pathlib import Path

      from pytest_cuke import given, parsers
      from pytest_cuke.formatter_api import FormatterRequest


      @given(parsers.parse("crash probe case {case} runs"))
      def crash_probe_case_runs(case):
          if case == "crash":
              os._exit(23)
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the survivor must run in an xdist worker"


      def pytest_cuke_formatter_requests(config):
          return (
              FormatterRequest(
                  name="worker-crash-temp-file-probe",
                  command=(
                  sys.executable,
                  "-c",
                  "import pathlib, sys; pathlib.Path('formatter-started.txt').write_text('started', encoding='utf-8'); "
                  "sys.stdin.read()",
                  ),
                  working_directory=Path.cwd(),
              ),
          )
      """
    And consumer file "features/crash-formatter-worker-cases.feature" contains:
      """gherkin
      Feature: Crashed worker during terminal formatter output
        Scenario: Crashed worker exits abruptly
          Given crash probe case crash runs

        Scenario: Remaining worker sends messages
          Given crash probe case survive runs
      """
    When I run installed pytest with a 45-second watchdog and arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features -n2 --dist=load --max-worker-restart=0 --color=no -q"
    Then pytest output should report the crashed xdist worker and partial Messages diagnostics
    And pytest should exit with a non-zero code
    And the consumer file "formatter-started.txt" should exist
    And consumer temporary directory "worker-messages-tmp" should have no worker-owned Messages stream files

  Scenario: A failing live batch publisher preserves accepted Messages in the final artifact
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import os

      from pytest_cuke import given, parsers


      @given(parsers.parse("batch publisher probe case {case} completes"))
      def batch_publisher_probe_case_completes(case):
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the batch publisher probe must run in an xdist worker"


      def pytest_cuke_message_batch(config, batch):
          raise RuntimeError("controlled live batch publisher failure")
      """
    And consumer file "features/batch-publisher-cases.feature" contains:
      """gherkin
      Feature: Batch publisher failures
        Scenario: First worker case
          Given batch publisher probe case alpha completes

        Scenario: Second worker case
          Given batch publisher probe case beta completes
      """
    When I run installed pytest with a 45-second watchdog and arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=publisher-failure.ndjson -n2 --dist=load --color=no -q"
    Then pytest output should contain "SINK_FAILURE"
    And pytest output should contain "controlled live batch publisher failure"
    And consumer artifact "publisher-failure.ndjson" should contain the accepted stream after a publisher failure
    And pytest should exit with code 1

  @external
  Scenario: Filesystem-isolated localhost gateways consolidate without the controller project path
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer pins pytest-xdist below 4 for socket rsync staging
    And a test-managed filesystem-isolated localhost execnet socket gateway is listening
    And consumer file "conftest.py" contains:
      """python
      import os
      from pathlib import Path

      from pytest_cuke import given, parsers


      @given(parsers.parse("isolated gateway case {case} completes"))
      def isolated_gateway_case_completes(case):
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the isolated socket gateway must execute this case"
          controller_root = Path(os.environ["PYTEST_CUKE_HIDDEN_CONSUMER_ROOT"])
          assert not controller_root.exists(), f"worker can still access controller project path: {controller_root}"
          assert Path(__file__).is_file(), "worker must execute the staged consumer conftest"
      """
    And consumer file "features/filesystem-isolated-gateway.feature" contains:
      """gherkin
      Feature: Filesystem-isolated socket gateway
        Scenario: First worker case
          Given isolated gateway case alpha completes

        Scenario: Second worker case
          Given isolated gateway case beta completes
      """
    When I run installed pytest through two localhost execnet socket gateways with arguments "--rootdir=. features/filesystem-isolated-gateway.feature --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=isolated.ndjson --dist=load --rsyncdir=. --color=no -q"
    Then pytest should exit with code 0
    And consumer artifact "isolated.ndjson" should be a complete filesystem-isolated gateway Messages stream

  Scenario: Two isolated localhost socket gateways consolidate Messages through xdist rsync
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer pins pytest-xdist below 4 for socket rsync staging
    And a test-managed isolated localhost execnet socket gateway is listening
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      import threading
      from pathlib import Path

      import pytest
      from pytest_cuke import given, parsers

      _consumer_config = None
      _observation_lock = threading.Lock()


      def pytest_configure(config):
          global _consumer_config
          _consumer_config = config


      @given(parsers.parse("worker case {case} completes"))
      def socket_worker_case_completes(case):
          assert os.environ.get("PYTEST_XDIST_WORKER"), "the socket gateway must execute the case in a worker"


      def pytest_cuke_message_batch(config, batch):
          messages_path = config.getoption("cuke_messages_ndjson")
          live_batches = Path(f"{messages_path}.live-batches.jsonl")
          with _observation_lock:
              with live_batches.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(batch, sort_keys=True) + "\n")


      @pytest.hookimpl(trylast=True)
      def pytest_testnodedown(node, error):
          worker_id = getattr(getattr(node, "gateway", None), "id", "unknown")
          worker_output = getattr(node, "workeroutput", {})
          record = {
              "worker_id": worker_id,
              "error": str(error) if error is not None else None,
              "exitstatus": worker_output.get("exitstatus"),
              "worker_output_keys": sorted(worker_output),
              "transport": worker_output.get("pytest_cuke_message_transport"),
          }
          messages_path = _consumer_config.getoption("cuke_messages_ndjson")
          manifests = Path(f"{messages_path}.worker-manifests.jsonl")
          with _observation_lock:
              with manifests.open("a", encoding="utf-8") as stream:
                  stream.write(json.dumps(record, sort_keys=True) + "\n")
      """
    And consumer file "features/socket-worker-cases.feature" contains:
      """gherkin
      Feature: Socket gateway cases
        Scenario: Standalone worker case completes
          Given worker case standalone completes

        Scenario Outline: Outline worker case <case> completes
          Given worker case <case> completes

        Examples:
          | case  |
          | alpha |
          | beta  |
          | alpha |
      """
    When I run installed pytest through two localhost execnet socket gateways with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=socket.ndjson --dist=load --rsyncdir=. --color=no -q"
    Then the test outcome should have 4 passed scenarios
    And consumer artifact "socket.ndjson.worker-manifests.jsonl" should report complete manifests matching "socket.ndjson.live-batches.jsonl"
    And consumer artifact "socket.ndjson" should be one complete localhost socket gateway Messages stream for the four selected rows
    And consumer artifact "socket.ndjson.live-batches.jsonl" should contain incomplete live worker batches
    And the socket consumer should have no worker-shared observation artifacts
    And pytest should exit with code 0
    And the installed consumer should have no leftover local Messages worker fragments
