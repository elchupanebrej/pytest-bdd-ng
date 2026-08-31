"""Regression tests for ordered tag-hook registration."""

from pytest_bdd.hook import after_tag, before_tag


def test_tag_hook_order_is_registered_on_the_fixture() -> None:
    """Expose the requested order to pytest's hook fixture boundary."""

    @before_tag("browser", order=-20)
    def before_browser(request: object) -> None:
        pass

    @after_tag("browser", order=30)
    def after_browser(request: object) -> None:
        pass

    assert before_browser.__pytest_bdd_hook_order__ == -20
    assert after_browser.__pytest_bdd_hook_order__ == 30
    before_fixture_name = before_browser.name
    after_fixture_name = after_browser.name
    assert "order_-0000000000000000020" in before_fixture_name
    assert "order_+0000000000000000030" in after_fixture_name


def test_tag_hooks_run_in_order(testdir) -> None:
    """Run matching tag hooks by their explicit order before the first step."""

    testdir.makefile(
        ".ini",
        pytest="""
            [pytest]
            markers =
                ordered
            """,
    )
    testdir.makefile(
        ".feature",
        ordered="""
            @ordered
            Feature: Ordered hooks
                Scenario: Runs ordered hooks
                    When run
            """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import when
        from pytest_bdd.hook import before_tag

        events = []

        @before_tag("@ordered", order=20)
        def second(request):
            events.append("second")

        @before_tag("@ordered", order=10)
        def first(request):
            events.append("first")

        @when("run")
        def run():
            print("HOOK_EVENTS", events)
        """,
    )

    result = testdir.runpytest("-s")

    result.assert_outcomes(passed=1)
    assert "HOOK_EVENTS ['first', 'second']" in result.stdout.str()
