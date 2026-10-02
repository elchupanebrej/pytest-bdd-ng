Feature files search is started from base directory
'''''''''''''''''''''''''''''''''''''''''''''''''''

By default, pytest-cuke will use current module's path as base path for
finding feature files, but this behaviour can be changed in the pytest
configuration file (i.e. ``pytest.ini``, ``tox.ini`` or ``setup.cfg``)
by declaring the new base path in the ``cuke_features_dir`` key. The
path is interpreted as relative to the pytest root directory. You can
also override features base path on a per-scenario basis, in order to
override the path for specific tests.

Background:


-  Given Localserver endpoint "/features/Passing.feature" responding
   content:

   ::

      Feature: Passing feature
        Scenario: Passing scenario
          Given Passing step
        Scenario: Failing scenario
          Given Failing step

-  And File "conftest.py" with content:

   ::

      from pytest_cuke import step
      from pytest_cuke.compatibility.pytest import fail

      @step('Passing step')
      def _():
        ...

      @step('Failing step')
      def _():
        fail('Intentional')

-  And File "test_feature.py" with content:

   ::

      from pytest_cuke import scenarios,FeaturePathType

      test = scenarios('Passing.feature', features_path_type=FeaturePathType.URL)

Scenario:


-  Given File "pytest.ini" with fixture templated content:

   ::

      [pytest]
      cuke_features_base_url=http://localhost:{httpserver_port}/features

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======
