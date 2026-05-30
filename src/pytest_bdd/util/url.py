"""Provide url helpers."""

from __future__ import annotations

from operator import attrgetter
from urllib.parse import urlparse


def is_local_url(urllike: object) -> bool:
    """
    Check if URL is a local file URL.

    Args:
        urllike: URL string or path-like object.

    Returns:
        True if URL is local (no scheme or netloc).

    """
    try:
        if not isinstance(urllike, (str, bytes, bytearray)):
            return False
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:  # noqa: BLE001 intentional
        return False


def is_url_parsable(urllike: object) -> bool:
    """
    Check if URL can be parsed.

    Args:
        urllike: URL string or path-like object.

    Returns:
        True if URL is parsable.

    """
    try:
        urlparse(str(urllike))
    except ValueError:
        return False
    else:
        return True
