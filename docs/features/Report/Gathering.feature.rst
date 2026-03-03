Feature: Report gathering outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents generation of machine-readable and HTML reports
during feature execution.

Background:
'''''''''''

-  Given File "Passing.feature" with content:

   .. code:: gherkin

      Feature: Passing feature
        Scenario: Passing scenario
          Given Passing step

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd import step

      @step('Passing step')
      def _():
        ...

Scenario: NDJson(JSONL) could be produced on the feature run
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Output file could be fed into other @cucumber tools for more verbose
report `Messages <https://github.com/cucumber/messages>`__

-  When run pytest

   .. raw:: html

        <!-- markdownlint-disable-next-line MD013 -->

   ========== ================= ==========
   cli_args   --messages-ndjson out.ndjson
   ========== ================= ==========
   subprocess true              
   ========== ================= ==========

-  Then File "out.ndjson" has at least "15" lines

-  Then Report "out.ndjson" parsable into messages

Scenario: HTML report could be produced on the feature run
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Dummy reporter based on
`@cucumber/html-formatter <https://github.com/cucumber/html-formatter>`__

-  Given Install npm packages

   ======== ========================
   packages @cucumber/html-formatter
   ======== ========================
   ======== ========================

-  When run pytest

   .. raw:: html

        <!-- markdownlint-disable-next-line MD013 -->

   +----------+------+----------+----+----------+----------+----------+
   | cli_args | -p   | no:pyt   | -p | pytes    | --cucum  | out.html |
   |          |      | est-bdd- |    | t_bdd.pl | ber-html |          |
   |          |      | gherkin- |    | ugin.ghe |          |          |
   |          |      | message- |    | rkin_mes |          |          |
   |          |      | reporter |    | sage_rep |          |          |
   |          |      |          |    | orter.en |          |          |
   |          |      |          |    | trypoint |          |          |
   +==========+======+==========+====+==========+==========+==========+
   | su       | true |          |    |          |          |          |
   | bprocess |      |          |    |          |          |          |
   +----------+------+----------+----+----------+----------+----------+

-  Then File "out.html" is not empty
