from __future__ import annotations

import re
from enum import Enum

TAG_PREFIX = "@"

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")

PYTEST_BDD_MARK = "pytest_bdd_scenario"


class FeatureAutoLoad:
    class Ini(Enum):
        DISABLE_OPTION = "disable_feature_autoload"
        CUCUMBER_JSON_PATH_OPTION = "cucumber_json_path"

    class Cli(Enum):
        DISABLE_OPTION = "feature_autoload"
        CUCUMBER_JSON_PATH_OPTION = "cucumber_json_path"


class FeatureBaseLoad:
    class Ini(Enum):
        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"


class CodeGeneration:
    class Cli(Enum):
        GENERATE_CODE = "generate"
        GENERATE_MISSING_CODE = "generate_missing"
        GENERATE_FROM_FEATURES = "features"
