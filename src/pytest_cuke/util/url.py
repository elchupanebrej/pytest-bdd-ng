from __future__ import annotations

from operator import attrgetter
from urllib.parse import urlparse


def is_local_url(urllike: object) -> bool:
    try:
        if not isinstance(urllike, str | bytes | bytearray):
            return False
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:
        return False


def is_url_parsable(urllike: object) -> bool:
    try:
        urlparse(str(urllike))
    except ValueError:
        return False
    else:
        return True
