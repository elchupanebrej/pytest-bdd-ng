"""Shared status mapping for native Allure API steps."""

from __future__ import annotations

import pytest


def _allure_api_step_status(
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
) -> str:
    """Map an exception from an ``allure.step`` body to its Allure status."""
    if exc_type is None and exc_val is None:
        return "passed"

    if exc_type is not None:
        exception_type = exc_type
    elif exc_val is not None:
        exception_type = type(exc_val)
    else:
        return "passed"

    if issubclass(exception_type, (pytest.skip.Exception, pytest.xfail.Exception)):
        return "skipped"
    if issubclass(exception_type, (AssertionError, pytest.fail.Exception)):
        return "failed"
    return "broken"
