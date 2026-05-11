"""
Public API for the Go gherkin parser backend.

Provides parse() function that mirrors gherkin.parser.Parser().parse() output.
"""

from __future__ import annotations

import json
import logging
import os

from pytest_bdd._gherkin_go._bridge import gherkin_go_available, parse_gherkin_document, parse_gherkin_markdown
from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError
from pytest_bdd.mimetype import Mimetype

logger = logging.getLogger(__name__)

_go_version_logged = False


def _should_use_go_backend() -> bool:
    """Check if Go backend should be attempted based on env var (single source of truth)."""
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()
    if backend == "python":
        return False
    if backend not in {"auto", "go"}:
        logger.warning("Unknown PYTEST_BDD_GHERKIN_BACKEND value '%s', treating as 'auto'", backend)
    return True


def _log_version() -> None:
    """Log the Go parser version on first successful use."""
    global _go_version_logged
    if _go_version_logged:
        return
    _go_version_logged = True
    try:
        from pytest_bdd._gherkin_go._bridge import gherkin_go_version  # noqa: PLC0415

        logger.info("Using Go gherkin parser %s", gherkin_go_version())
    except Exception:
        logger.debug("Failed to retrieve Go parser version", exc_info=True)


def parse(text: str, *, mimetype: Mimetype) -> dict:
    """
    Parse Gherkin text, returning dict identical to Python Parser().parse().

    Args:
        text: Gherkin (or Markdown+Gherkin) feature content.
        mimetype: Determines plain vs markdown parsing mode.

    Returns:
        Dict with 'type': 'GherkinDocument' and 'feature' key.

    Raises:
        GherkinParseError: On invalid Gherkin syntax.
        GherkinGoNotAvailable: When Go parser is unavailable in 'go' mode.

    """
    if not gherkin_go_available():
        msg = "Go shared library not found in package data"
        logger.warning("Go gherkin parser unavailable (%s), falling back to Python", msg)
        raise GherkinGoNotAvailable(msg)

    json_str = parse_gherkin_markdown(text) if mimetype == Mimetype.gherkin_markdown else parse_gherkin_document(text)

    result = json.loads(json_str)
    if isinstance(result, list):
        raise GherkinParseError(result)

    _log_version()
    return result
