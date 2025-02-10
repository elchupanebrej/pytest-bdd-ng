from pytest import Config

from pytest_bdd.compatibility.pytest import Parser
from pytest_bdd.const import FeatureAutoLoad


def is_enabled(config: Config):
    is_enabled = config.getoption(FeatureAutoLoad.Cli.DISABLE_OPTION.value)
    if is_enabled is None:
        is_enabled = not config.getini(FeatureAutoLoad.Ini.DISABLE_OPTION.value)
    return is_enabled


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    group.addoption(
        "--disable-feature-autoload",
        action="store_false",
        dest=FeatureAutoLoad.Cli.DISABLE_OPTION.value,
        default=None,
        help="Turn off feature files autoload",
    )
    parser.addini(
        FeatureAutoLoad.Ini.DISABLE_OPTION.value,
        default=False,
        type="bool",
        help="Turn off feature files autoload",
    )
