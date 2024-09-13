#################
Developer Guide
#################

.. _quickstart: https://docs.dagger.io/quickstart/729236/cli

This section is introduced specifically for ``pytest-bdd-ng`` to help developers maintain and enhance the source code.


Reduce dependence on Github Actions
===================================

Currently the Github action can take as much as 29 minutes and it has pinned [dependencies in other repos](https://github.com/blaisep/pytest-bdd-ng/blob/default/.github/workflows/main.yml#L33).

I intend to implement local CI so that:
- We can easily rotate external dependencies
- We can iterate faster (by caching intermediate artifacts)
- Developers can follow the dependency tree more easily. (gitmodules don't get cloned locally)


Building the project locally
############################

Prepare your virtual environment
================================

To build the project locally, these instructions assume that you already have a working:
    - installed a docker runtime (eg. Docker, Rancher, Orbstack, etc)
    - dagger CLI (eg ``brew install dagger/tap/dagger``)
    - dagger Python SDK in your virtualenv (eg. ``pip install -U dagger-io``)
You can refer to the dagger quickstart_  docs for help installing dagger.


Explore dagger
==============

Let's have a bit of fun exploring dagger. Create ``ci/main.py`` and paste the following code.

.. code-block::python

    import sys
    import anyio
    import dagger

    """
    Run directory listing of the files in the build container
    """

    async def main():
        async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            out = await (
                client.container()
                .from_("python:3.11-slim")
                .with_directory("/host", client.host().directory("."))
                .with_exec(["ls", "-al", "."])
                .stdout()
            )
        print(out)
    anyio.run(main)

Now run ``dagger run python ci/main.py``
Note the total time on the last line of the console input.

Run the command again and note the total time. It should be much faster.

Next, change the line ``.with_exec(["ls", "-al", "/host"])`` to ``.with_exec(["ls", "-al", "/host/tests"])``
and run ``dagger run python ci/main.py``

Is the directory listing different? How about the total time?
