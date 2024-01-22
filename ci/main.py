import sys

import anyio

import dagger

"""
Copy files to the build container and list them.
"""
async def main():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        out = await (
            client.container()
            .from_("python:3.11-slim")
            .with_directory("/host", client.host().directory("."))
            .with_exec(["ls", "-al", "/host"])
            .stdout()
        )

    print(out)

anyio.run(main)
