import os
import plistlib


def read(path):
    """return webloc url"""
    with open(path, "rb") as f:
        return plistlib.load(f).get("URL")


def write(path, url):
    """write url to webloc file"""
    data = dict(URL=str(url))
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(path, "wb") as f:
        plistlib.dump(data, f)
