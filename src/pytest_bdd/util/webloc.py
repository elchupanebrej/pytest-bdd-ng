import os
import plistlib


def read(path):
    """Return webloc url"""
    if hasattr(plistlib, "load"):
        with open(path, "rb") as f:
            return plistlib.load(f).get("URL")
    return plistlib.readPlist(path).get("URL")


def write(path, url):
    """Write url to webloc file"""
    data = {"URL": str(url)}
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    if hasattr(plistlib, "dump"):
        with open(path, "wb") as f:
            plistlib.dump(data, f)
    else:
        plistlib.writePlist(data, path)
