import plistlib
from pathlib import Path


def read(path: str | Path) -> str | None:
    """Return the URL stored in a macOS web location file."""
    with Path(path).open("rb") as source:
        data = plistlib.load(source)
    url = data.get("URL") if isinstance(data, dict) else None
    return url if isinstance(url, str) else None


def write(path: str | Path, url: str) -> None:
    """Write a URL to a macOS web location file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as target:
        plistlib.dump({"URL": url}, target)
