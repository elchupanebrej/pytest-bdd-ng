Feature:
^^^^^^^^

Background:
'''''''''''

-  Given File "Passing.feature" with content:

   ::

      Feature: Passing feature
        Scenario: Passing scenario
          Given Passing step

-  And File "conftest.py" with content:

   ::

      from pytest_cuke import step

      @step('Passing step')
      def _():
        ...

Scenario: NDJson(JSONL) could be produced on the feature run
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

::

   Output file could be fed into other @cucumber tools for more verbose report
   [Messages](https://github.com/cucumber/messages)

-  When I run pytest in a subprocess with arguments
   "--cuke-messages-ndjson out.ndjson"

-  Then Report "out.ndjson" parsable into messages

-  Then Messages report file "out.ndjson" contains one complete
   successful run with one scenario and one passed step

Scenario: HTML report could be produced on the feature run
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

::

   Dummy reporter based on [@cucumber/html-formatter](https://github.com/cucumber/html-formatter)

-  Given Install npm packages

   ======== ========================
   packages @cucumber/html-formatter
   ======== ========================
   ======== ========================

-  When I run pytest in a subprocess with arguments "--cuke-html
   out.html"

-  Then File "out.html" is not empty
