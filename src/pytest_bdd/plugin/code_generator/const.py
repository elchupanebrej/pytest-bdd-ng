"""Provide const helpers."""

from enum import Enum


class CodeGeneration:
    """Represent code generation state."""

    class Cli(Enum):
        """CLI option values for code generation."""

        GENERATE_CODE = "generate"
        GENERATE_MISSING_CODE = "generate_missing"
        GENERATE_FROM_FEATURES = "features"
