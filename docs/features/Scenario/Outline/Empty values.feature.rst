Feature: Outline empty values
'''''''''''''''''''''''''''''

This feature documents scenario outline behavior when examples include
empty values and verifies placeholder values are passed exactly as text,
including empty strings.

Scenario: Scenario outline accepts empty example values
                                                       

-  Given File "outline.feature" with content:

   .. code:: gherkin

      Feature: Outline
        Scenario Outline: Outlined with empty example values
          Given there are <start> cucumbers
          When I eat <eat> cucumbers
          Then I should have <left> cucumbers

          Examples:
            | start | eat | left |
            | #     |     |      |

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd import given, when, then, parsers

      @given(parsers.re("there are (?P<start>.*?) cucumbers"), target_fixture="captured")
      def _start_cucumbers(start):
        return {"start": start}

      @when(parsers.re("I eat (?P<eat>.*?) cucumbers"))
      def _eat_cucumbers(captured, eat):
        captured["eat"] = eat

      @then(parsers.re("I should have (?P<left>.*?) cucumbers"))
      def _left_cucumbers(captured, left):
        captured["left"] = left
        assert captured == {"start": "#", "eat": "", "left": ""}

-  And File "test_outline.py" with content:

   .. code:: python

      from pytest_bdd import scenarios

      test_outline = scenarios('outline.feature')

-  When run pytest

   \| cli_args \| -k \| test_outline.py \|

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      0
   ====== ======
