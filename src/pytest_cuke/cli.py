"""Standalone command line interface for pytest-cuke.

Third party distributions can extend the command tree by registering an entry
point in the ``pytest_cuke.commands`` group. Each entry point must load a
callable that accepts a :class:`CommandRegistry` and registers one or more
commands with :meth:`CommandRegistry.add`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import cast

from pytest_cuke.heading_validation_cli import configure_validation_parser, run_validation_command
from pytest_cuke.packaging import get_distribution_version

CommandHandler = Callable[[Sequence[str]], int]
NamespaceCommandHandler = Callable[[argparse.Namespace], int]
ParserConfigurer = Callable[[argparse.ArgumentParser], None]


@dataclass(frozen=True)
class CommandSpec:
    """A registered leaf command in the pytest-cuke command tree."""

    path: tuple[str, ...]
    help: str
    handler: CommandHandler | None
    positionals: tuple[str, ...] = ()
    parser_configurer: ParserConfigurer | None = None
    namespace_handler: NamespaceCommandHandler | None = None


@dataclass
class _CommandGroup:
    children: dict[str, _CommandGroup | CommandSpec] = field(default_factory=dict)


class CommandRegistry:
    """Collect built-in and extension commands before rendering CLI help."""

    def __init__(self) -> None:
        self._commands: dict[tuple[str, ...], CommandSpec] = {}

    def add(
        self,
        path: Sequence[str],
        help: str,
        handler: CommandHandler | None,
        *,
        positionals: Sequence[str] = (),
        parser_configurer: ParserConfigurer | None = None,
        namespace_handler: NamespaceCommandHandler | None = None,
    ) -> None:
        """Register a command path and its handler.

        ``path`` must contain at least one command name, such as
        ``("check", "manifest")``. Handlers receive the arguments following
        their command path and return the process exit code. A command may
        declare required positional arguments, which are shown in help and
        passed to its handler in order.
        """
        normalized_path = tuple(part.strip() for part in path)
        if not normalized_path or any(not part or part.startswith("-") for part in normalized_path):
            raise ValueError("command paths must contain non-empty positional names")
        normalized_positionals = tuple(argument.strip() for argument in positionals)
        positional_destinations = tuple(argument.replace("-", "_") for argument in normalized_positionals)
        if any(
            not argument or argument.startswith("-") or not destination.isidentifier()
            for argument, destination in zip(normalized_positionals, positional_destinations, strict=True)
        ):
            raise ValueError("positional arguments must be valid non-empty names")
        if len(set(positional_destinations)) != len(positional_destinations):
            raise ValueError("positional arguments must have unique names")
        if (handler is None) == (namespace_handler is None):
            raise ValueError("register exactly one command handler")
        if normalized_path in self._commands:
            raise ValueError(f"command already registered: {' '.join(normalized_path)}")
        if any(existing[: len(normalized_path)] == normalized_path for existing in self._commands):
            raise ValueError(f"command path already has registered children: {' '.join(normalized_path)}")
        if any(normalized_path[: len(existing)] == existing for existing in self._commands):
            raise ValueError(f"command path conflicts with registered parent: {' '.join(normalized_path)}")
        self._commands[normalized_path] = CommandSpec(
            normalized_path,
            help,
            handler,
            normalized_positionals,
            parser_configurer,
            namespace_handler,
        )

    @property
    def commands(self) -> tuple[CommandSpec, ...]:
        """Return the registered leaf commands in stable display order."""
        return tuple(self._commands[path] for path in sorted(self._commands))


def _unimplemented(path: str) -> CommandHandler:
    def run(arguments: Sequence[str]) -> int:
        del arguments
        print(f"cuke {path}: this command is not implemented yet", file=sys.stderr)
        return 2

    return run


def _build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.add(
        ("validate",),
        "validate feature files",
        None,
        positionals=("features-dir",),
        parser_configurer=configure_validation_parser,
        namespace_handler=run_validation_command,
    )
    registry.add(("generate", "steps"), "generate step definition stubs", _unimplemented("generate steps"))
    registry.add(("convert", "allure"), "convert Allure results", _unimplemented("convert allure"))

    for extension in entry_points(group="pytest_cuke.commands"):
        register_commands = extension.load()
        if not callable(register_commands):
            raise TypeError(f"pytest-cuke command extension {extension.name!r} is not callable")
        register_commands(registry)
    return registry


def _parser_for(registry: CommandRegistry, program: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=program,
        description="Run pytest-cuke product commands.",
        epilog=(
            "Command extensions register through the pytest_cuke.commands entry-point group. "
            "Each entry point loads a function that receives a CommandRegistry."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pytest-cuke {get_distribution_version('pytest-cuke')}",
    )
    tree = _CommandGroup()
    for command in registry.commands:
        branch = tree
        for name in command.path[:-1]:
            child = branch.children.setdefault(name, _CommandGroup())
            if isinstance(child, CommandSpec):
                raise ValueError(f"command group conflicts with leaf command: {name}")
            branch = child
        branch.children[command.path[-1]] = command

    def add_commands(command_parser: argparse.ArgumentParser, branches: _CommandGroup) -> None:
        subparsers = command_parser.add_subparsers(metavar="COMMANDS")
        for name, branch in sorted(branches.children.items()):
            if isinstance(branch, CommandSpec):
                invocation = _command_invocation(branch)
                child_parser = subparsers.add_parser(
                    name,
                    help=f"{invocation} — {branch.help}",
                    description=branch.help,
                )
                if branch.positionals:
                    for positional in branch.positionals:
                        child_parser.add_argument(positional.replace("-", "_"), metavar=positional)
                elif branch.namespace_handler is None:
                    child_parser.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
                if branch.parser_configurer is not None:
                    branch.parser_configurer(child_parser)
                child_parser.set_defaults(
                    _cuke_handler=branch.handler,
                    _cuke_namespace_handler=branch.namespace_handler,
                    _cuke_positionals=branch.positionals,
                )
            else:
                first_command = next(_iter_commands(branch))
                invocation = _command_invocation(first_command)
                child_parser = subparsers.add_parser(name, help=f"{invocation} — {first_command.help}")
                add_commands(child_parser, branch)

    add_commands(parser, tree)
    return parser


def _command_invocation(command: CommandSpec) -> str:
    return " ".join((*command.path, *(f"<{argument}>" for argument in command.positionals)))


def _iter_commands(branches: _CommandGroup) -> Iterator[CommandSpec]:
    for branch in branches.children.values():
        if isinstance(branch, CommandSpec):
            yield branch
        else:
            yield from _iter_commands(branch)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected command and return its process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    program = "pytest-cuke" if "pytest-cuke" in sys.argv[0] else "cuke"
    parser = _parser_for(_build_registry(), program)
    namespace = parser.parse_args(arguments)
    namespace_handler = cast("NamespaceCommandHandler | None", getattr(namespace, "_cuke_namespace_handler", None))
    if namespace_handler is not None:
        return namespace_handler(namespace)
    handler = cast("CommandHandler | None", getattr(namespace, "_cuke_handler", None))
    if handler is None:
        parser.print_help()
        return 0 if not arguments else 2
    handler_arguments = getattr(namespace, "arguments", None)
    if handler_arguments is None:
        handler_arguments = [
            getattr(namespace, positional.replace("-", "_"))
            for positional in getattr(namespace, "_cuke_positionals", ())
        ]
    return handler(handler_arguments)


if __name__ == "__main__":
    raise SystemExit(main())
