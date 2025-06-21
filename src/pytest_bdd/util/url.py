from operator import attrgetter
from urllib.parse import urlparse


def is_local_url(urllike):
    try:
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:  # noqa: BLE001 intentional
        return False


def is_url_parsable(urllike):
    try:
        urlparse(str(urllike))
        return True
    except ValueError:
        return False
