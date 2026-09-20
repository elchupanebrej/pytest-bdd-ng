"""Test feature background."""

from pytest import mark

pytestmark = mark.integration


# language=gherkin
FEATURE = '''\
    Feature: Some rules
        """
        Feature description
        """

      Background:
        """
        Background description
        """
        Given fb
          """
          Step description
          """

      Rule: A
        The rule A description

        Background:
          Given ab

        Example: Example A
          Given a

      Rule: B
        The rule B description

        Example: Example B
          Given b

      Rule: C
        The rule C description

        Example: Example CA
          Given c

        Rule: CB
            Example: CBA
              Given caa

            Example: CBB
              Given cab

            Example: CBC
              Given ca<key>

              Examples:
              | key |
              |  c  |
              |  d  |
              |  e  |
'''

# language=python
STEPS = """\
    from pytest_bdd import given

    @given("{}")
    def step():
        pass
"""

# language=gherkin
MERGE_FEATURE = '''\
Feature: Rule background merge

  Background:
    Given feature background step

  Rule: A
    Background:
      Given rule background step

    Example: Example A
      Given scenario step
'''

# language=python
MERGE_STEPS = """\
from pytest import fixture

from pytest_bdd import given


@fixture
def executed():
    return []


@given("feature background step")
def feature_background_step(executed):
    executed.append("feature")


@given("rule background step")
def rule_background_step(executed):
    executed.append("rule")


@given("scenario step")
def scenario_step(executed):
    executed.append("scenario")
"""


def test_background_basic(testdir):
    """Test feature background."""
    testdir.makefile(".feature", rule=FEATURE)

    testdir.makeconftest(STEPS)

    result = testdir.runpytest()
    result.assert_outcomes(passed=8)


def test_rule_background_merges_with_feature_background(testdir, tmp_path):
    """Feature background steps run first, then rule background steps."""
    feature_path = tmp_path / "rule-merge.feature"
    feature_path.write_text(MERGE_FEATURE)

    testdir.makeconftest(MERGE_STEPS)

    testdir.makepyfile(
        f"""\
        from pathlib import Path

        from pytest_bdd import scenario

        @scenario(Path(r"{feature_path}"), "Example A")
        def test_merged_backgrounds(executed):
            assert executed == ["feature", "rule", "scenario"]
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
