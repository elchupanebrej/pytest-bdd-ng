from importlib.metadata import PackageNotFoundError

import pytest

from scripts.check_types import TypecheckConfigurationError, _validate_distributions


@pytest.mark.parametrize(
    ("available", "missing"),
    [
        ({"attrs": "26.1.0", "pydantic": "2.12.5", "tomli": "2.2.1"}, "types-PyYAML"),
        ({"attrs": "26.1.0", "pydantic": "2.12.5", "types-PyYAML": "6.0.12.20260906"}, "tomli"),
        ({"attrs": "26.1.0", "tomli": "2.2.1", "types-PyYAML": "6.0.12.20260906"}, "pydantic"),
        ({"pydantic": "2.12.5", "tomli": "2.2.1", "types-PyYAML": "6.0.12.20260906"}, "attrs"),
    ],
)
def test_missing_required_typing_support_has_an_actionable_error(available: dict[str, str], missing: str) -> None:
    def package_version(distribution: str) -> str:
        if distribution == "mypy":
            return "2.3.1"
        try:
            return available[distribution]
        except KeyError as error:
            raise PackageNotFoundError(distribution) from error

    with pytest.raises(TypecheckConfigurationError, match=f"Required typing distribution '{missing}' is missing"):
        _validate_distributions(
            "2.3.1",
            (
                "attrs==26.1.0",
                "pydantic==2.12.5",
                "tomli==2.2.1",
                "types-PyYAML==6.0.12.20260906",
            ),
            version_lookup=package_version,
        )


def test_required_framework_version_mismatch_has_an_actionable_error() -> None:
    def package_version(distribution: str) -> str:
        versions = {
            "mypy": "2.3.1",
            "attrs": "26.1.0",
            "pydantic": "2.13.5",
            "tomli": "2.2.1",
            "types-PyYAML": "6.0.12.20260906",
        }
        return versions[distribution]

    with pytest.raises(TypecheckConfigurationError, match=r"pydantic.*must be version 2.12.5"):
        _validate_distributions(
            "2.3.1",
            (
                "attrs==26.1.0",
                "pydantic==2.12.5",
                "tomli==2.2.1",
                "types-PyYAML==6.0.12.20260906",
            ),
            version_lookup=package_version,
        )
