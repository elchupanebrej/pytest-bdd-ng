from pytest_cuke.message_plugin import session_hook_name


def test_controller_run_hooks_keep_the_plain_name():
    assert session_hook_name("before", None) == "pytest session start"
    assert session_hook_name("after", None) == "pytest session finish"


def test_worker_run_hooks_are_identified_by_their_worker():
    assert session_hook_name("before", "gw0") == "pytest session start (gw0)"
    assert session_hook_name("after", "gw1") == "pytest session finish (gw1)"
