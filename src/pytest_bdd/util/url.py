from urllib.parse import urlparse

from _operator import attrgetter


def is_local_url(urllike):
    try:
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:
        return False


def is_url_parsable(urllike):
    try:
        urlparse(str(urllike))
        return True
    except ValueError:
        return False
