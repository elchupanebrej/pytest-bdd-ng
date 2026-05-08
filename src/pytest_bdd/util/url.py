"""Provide url helpers."""

from __future__ import annotations

from operator import attrgetter
from urllib.parse import urlparse


def is_local_url(urllike: object) -> bool:
    """Return local url."""
    try:
        if not isinstance(urllike, (str, bytes, bytearray)):
            return False
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:  # noqa: BLE001 intentional
        return False


def is_url_parsable(urllike: object) -> bool:
    """Return url parsable."""
    try:
        urlparse(str(urllike))
    except ValueError:
        return False
    else:
        return True
