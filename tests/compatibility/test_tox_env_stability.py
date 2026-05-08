"""Provide test tox env stability helpers."""

from pytest_bdd.compatibility.matrix import build_matrix, expand_tox_env_names


def test_tox_env_name_format_is_stable():
    """Verify tox env name format is stable."""
    entries = build_matrix(["313"], ["83", "90"])
    env_names = expand_tox_env_names(entries)

    for env_name in env_names:
        assert env_name.startswith("py")
        assert "-pytest" in env_name
        assert env_name.endswith("-coverage-lin")
