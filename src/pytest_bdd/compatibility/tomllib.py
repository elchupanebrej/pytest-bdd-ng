import sys

if sys.version_info < (3, 11):
    from tomli import TOMLDecodeError, load, loads
else:
    from tomllib import TOMLDecodeError, load, loads

__all__ = ("TOMLDecodeError", "load", "loads")
