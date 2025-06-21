import plistlib
from pathlib import Path


def read(path):
    """Return webloc url"""
    if hasattr(plistlib, "load"):
        with Path(path).open("rb") as f:
            return plistlib.load(f).get("URL")
    return plistlib.readPlist(path).get("URL")


def write(path, url):
    """Write url to webloc file"""
    data = {"URL": str(url)}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if hasattr(plistlib, "dump"):
        with Path(path).open("wb") as f:
            plistlib.dump(data, f)
    else:
        plistlib.writePlist(data, path)
