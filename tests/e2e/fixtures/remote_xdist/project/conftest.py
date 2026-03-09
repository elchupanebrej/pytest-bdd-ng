# This package is a test fixture project executed inside Docker containers /
# subprocesses by test_xdist_remote_message_aggregation.py.
# It must NOT be collected by the top-level pytest session.

collect_ignore_glob = ["*.feature"]
