from enum import Enum


class CodeGeneration:
    class Cli(Enum):
        """CLI option values for code generation."""

        GENERATE_CODE = "generate"
        GENERATE_MISSING_CODE = "generate_missing"
        GENERATE_FROM_FEATURES = "features"
