"""Quality gate behavioral tests for BLQ901, BLQ902, and plugin_patterns integration."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

from pytest_bdd._ruff.rules.quality_gates import (
    QualityGateVisitor,
    check_file,
)

SRC_ROOT = Path("src/pytest_bdd")


def _check_source(source: str, filename: str = "<test>") -> list:
    """Run quality gate visitor on source string, return violations."""
    tree = ast.parse(source, filename=filename)
    visitor = QualityGateVisitor(Path(filename), source.splitlines())
    visitor.visit(tree)
    return visitor.violations


class TestBLQ901ReturnNone:
    """Tests for BLQ901: return None in non-hook functions."""

    def test_detects_return_none_in_plain_function(self):
        """BLQ901 flags return None in a regular function."""
        source = textwrap.dedent("""\
            def lookup(key):
                if key in data:
                    return data[key]
                return None
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 1
        assert blq901[0].line == 4

    def test_exempts_pytest_hook_functions(self):
        """BLQ901 exempts functions starting with pytest_."""
        source = textwrap.dedent("""\
            def pytest_collect_file(path, parent):
                if path.ext == ".feature":
                    return FeatureFileModule.from_parent(parent, path=path)
                return None
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 0

    def test_exempts_private_pytest_hook_functions(self):
        """BLQ901 exempts functions starting with _pytest_."""
        source = textwrap.dedent("""\
            def _pytest_configure_hook(config):
                if not hasattr(config, "bdd"):
                    return None
                config.bdd.setup()
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 0

    def test_detects_return_none_in_nested_function(self):
        """BLQ901 flags return None in nested (non-hook) functions."""
        source = textwrap.dedent("""\
            def outer():
                def inner():
                    return None
                return inner()
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 1
        assert blq901[0].line == 3

    def test_no_violation_for_return_value(self):
        """Returning a non-None value does not trigger BLQ901."""
        source = textwrap.dedent("""\
            def lookup(key):
                if key in data:
                    return data[key]
                return "default"
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 0

    def test_no_violation_for_implicit_return(self):
        """Implicit return (no return statement) does not trigger BLQ901."""
        source = textwrap.dedent("""\
            def do_something():
                x = 1
                y = 2
        """)
        violations = _check_source(source)
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 0

    def test_clean_pass_against_current_codebase(self):
        """Quality gate runs clean against current src/pytest_bdd/."""
        violations = check_file(SRC_ROOT / "steps" / "registry.py")
        blq901 = [v for v in violations if "BLQ901" in v.message]
        assert len(blq901) == 0, f"BLQ901 violations in registry.py: {blq901}"


class TestBLQ902BareExcept:
    """Tests for BLQ902: bare except Exception without logging."""

    def test_detects_bare_except_without_logging(self):
        """BLQ902 flags except Exception without logging."""
        source = textwrap.dedent("""\
            def parse():
                try:
                    do_stuff()
                except Exception:
                    pass
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 1
        assert blq902[0].line == 4

    def test_exempts_noqa_ble001_comment(self):
        """BLQ902 exempts except handlers with # noqa: BLE001."""
        source = textwrap.dedent("""\
            def is_valid(url):
                try:
                    urlparse(url)
                    return True
                except Exception:  # noqa: BLE001
                    return False
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0

    def test_exempts_noqa_blq902_comment(self):
        """BLQ902 exempts except handlers with # noqa: BLQ902."""
        source = textwrap.dedent("""\
            def parse():
                try:
                    do_stuff()
                except Exception:  # noqa: BLQ902
                    pass
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0

    def test_exempts_logger_warning_with_exc_info(self):
        """BLQ902 exempts except handlers with logger.warning(exc_info=True)."""
        source = textwrap.dedent("""\
            import logging
            logger = logging.getLogger(__name__)

            def parse():
                try:
                    do_stuff()
                except Exception:
                    logger.warning("parse failed", exc_info=True)
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0

    def test_exempts_logger_exception_call(self):
        """BLQ902 exempts except handlers with logger.exception()."""
        source = textwrap.dedent("""\
            import logging
            logger = logging.getLogger(__name__)

            def parse():
                try:
                    do_stuff()
                except Exception:
                    logger.exception("parse failed")
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0

    def test_noqa_on_previous_line_exempts(self):
        """BLQ902 exempts when # noqa: BLE001 is on the line above."""
        source = textwrap.dedent("""\
            def parse():
                try:
                    do_stuff()
                # noqa: BLE001
                except Exception:
                    pass
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0

    def test_specific_exception_not_flagged(self):
        """except ValueError is not flagged by BLQ902."""
        source = textwrap.dedent("""\
            def parse():
                try:
                    int("bad")
                except ValueError:
                    pass
        """)
        violations = _check_source(source)
        blq902 = [v for v in violations if "BLQ902" in v.message]
        assert len(blq902) == 0


class TestPluginPatternsIntegration:
    """Tests that quality_gates includes plugin_patterns validation."""

    def test_quality_gates_main_run_includes_plugin_patterns(self) -> None:
        """quality_gates.main checks plugin dir when at default location."""
        violations = check_file(SRC_ROOT / "_ruff" / "rules" / "quality_gates.py")
        plugin_violations = [v for v in violations if "BLQ1001" in v.message]
        assert len(plugin_violations) == 0, "BLQ1001 should not fire on quality_gates.py itself"

    def test_plugin_patterns_pass_on_real_codebase(self) -> None:
        """Plugin patterns check passes clean on the actual codebase."""
        from pytest_bdd._ruff.rules.plugin_patterns import check_plugin_patterns

        plugin_root = SRC_ROOT / "plugin"
        violations = check_plugin_patterns(plugin_root)
        assert violations == [], f"Expected zero plugin pattern violations, got {len(violations)}"
