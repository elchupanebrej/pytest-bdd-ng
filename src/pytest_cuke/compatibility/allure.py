from __future__ import annotations

import importlib.util

ALLURE_INSTALLED = (
    importlib.util.find_spec("allure_commons") is not None and importlib.util.find_spec("allure_pytest") is not None
)

__all__ = ["ALLURE_INSTALLED"]
