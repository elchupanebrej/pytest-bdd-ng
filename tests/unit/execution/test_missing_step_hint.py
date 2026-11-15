from types import SimpleNamespace

from pytest_cuke.runner import missing_step_hint


def test_missing_step_hint_renders_a_python_stub_without_node():
    hint = missing_step_hint(SimpleNamespace(name="I have 5 apples", keyword="Given"))

    assert "from pytest_cuke import given" in hint
    assert '@given("I have 5 apples")' in hint
    assert "def step_i_have_5_apples():" in hint
    assert 'raise NotImplementedError("Implement step: I have 5 apples")' in hint


def test_missing_step_hint_escapes_quotes_and_uses_generic_step_for_and():
    hint = missing_step_hint(SimpleNamespace(name='say "hello"', keyword="And"))

    assert "from pytest_cuke import step" in hint
    assert '@step("say \\"hello\\"")' in hint
    assert "def step_say_hello():" in hint
