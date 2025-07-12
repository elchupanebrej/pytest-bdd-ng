import sys

GlobError = IndexError if sys.version_info < (3, 13) else ValueError
