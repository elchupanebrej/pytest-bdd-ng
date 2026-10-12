"""Standalone transactional step-generation command."""

from __future__ import annotations

import argparse
import ast
import glob
import hashlib
import importlib
import importlib.util
import os
import sys
import tempfile
import warnings
from contextlib import redirect_stderr, redirect_stdout, suppress
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import SplitResult, urlsplit
from urllib.request import url2pathname
from uuid import uuid4

import pytest

import pytest_cuke
from pytest_cuke.compatibility.pytest import PYTEST7
from pytest_cuke.generation import (
    STEP_TYPE_TO_STEP_METHOD_NAME,
    StepDefinitionInspectionError,
    iter_step_definition_matches,
    make_python_docstring,
)
from pytest_cuke.model.step import Step, StepType
from pytest_cuke.scenario_locator import FileScenarioLocator
from pytest_cuke.source_editor import SourceEditError, update_source_file
from pytest_cuke.utils import make_python_name
from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable, Sequence
    from types import ModuleType

    from pytest_cuke.compatibility.pytest import Session
    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.source_editor import SourceEditResult


class GenerationCommandError(RuntimeError):
    """A generation request cannot be completed safely."""


def configure_generate_steps_parser(parser: argparse.ArgumentParser) -> None:
    """Register the public options for ``cuke generate steps``."""
    parser.add_argument(
        "--feature",
        action="append",
        required=True,
        metavar="PATH",
        help="feature file, directory, or glob to inspect; repeat to select more than one",
    )
    parser.add_argument("--target", type=Path, metavar="PYTHON_FILE", help="update this existing Python module")
    parser.add_argument("--preview", action="store_true", help="show a diff without changing the target")
    parser.add_argument(
        "--keep-on-error",
        action="store_true",
        help="keep the attempted source update if formatting or validation fails",
    )
    parser.add_argument(
        "--bind-scenarios",
        action="store_true",
        help="also add missing scenario bindings to the selected target module",
    )


def run_generate_steps(namespace: argparse.Namespace) -> int:
    """Inspect selected features and print or transactionally apply additions."""
    try:
        if namespace.preview and namespace.target is None:
            raise GenerationCommandError("--preview requires --target")
        if namespace.keep_on_error and namespace.target is None:
            raise GenerationCommandError("--keep-on-error requires --target")
        if namespace.bind_scenarios and namespace.target is None:
            raise GenerationCommandError("--bind-scenarios requires --target")

        features = _load_features(cast("Sequence[str]", namespace.feature))
        steps = _unique_steps(features)
        if namespace.target is None:
            source = _render_additions(steps, (), None, None)
            if source:
                print(source, end="")
            else:
                print("No steps found in the selected features.")
            return 0

        target = cast("Path", namespace.target).expanduser()
        try:
            target = target.resolve(strict=True)
        except OSError as error:
            raise GenerationCommandError(f"target file does not exist: {target}") from error
        if not target.is_file() or target.suffix.casefold() != ".py":
            raise GenerationCommandError(f"target must be an existing Python file: {target}")

        module, syntax_tree = _load_target_module(target)
        missing_steps, project_root, features_base_dir = _missing_steps(features, module, target)
        missing_scenarios = (
            _missing_scenarios(features, module, target, project_root, features_base_dir)
            if namespace.bind_scenarios
            else []
        )
        source = _render_additions(missing_steps, missing_scenarios, module, syntax_tree, target=target)
        result = update_source_file(
            target,
            source,
            preview=namespace.preview,
            keep_on_error=namespace.keep_on_error,
        )
        _report_result(result, target, len(missing_steps), len(missing_scenarios), namespace.preview)
        return 0
    except (GenerationCommandError, SourceEditError, OSError, SyntaxError, ValueError) as error:
        print(f"cuke generate steps: {error}", file=sys.stderr)
        return 2


def _load_features(feature_arguments: Sequence[str]) -> list[Feature]:
    paths: list[str | Path] = []
    for raw_argument in feature_arguments:
        expanded_argument = Path(raw_argument).expanduser()
        if glob.has_magic(raw_argument):
            matches = glob.glob(str(expanded_argument))
            if not matches:
                raise GenerationCommandError(f"feature path pattern matched no files: {raw_argument}")
            paths.extend(matches)
        elif expanded_argument.exists():
            paths.append(expanded_argument)
        else:
            raise GenerationCommandError(f"feature file or directory does not exist: {raw_argument}")

    try:
        features = list(FileScenarioLocator(feature_paths=paths, features_base_dir=Path.cwd()).resolve_features())
    except Exception as error:
        raise GenerationCommandError(f"could not parse selected features: {error}") from error
    if not features:
        raise GenerationCommandError("no supported feature files were found in the selected paths")
    return features


def _load_target_module(target: Path) -> tuple[ModuleType, ast.Module]:
    source = target.read_bytes()
    try:
        compile(source, str(target), "exec")
        syntax_tree = ast.parse(source, filename=str(target))
    except (SyntaxError, ValueError, UnicodeError) as error:
        raise GenerationCommandError(f"existing target is not valid Python: {error}") from error

    package_name, import_root = _package_context(target)
    module_name = (
        f"{package_name}.{target.stem}"
        if package_name
        else (f"_pytest_cuke_generation_{hashlib.sha256(str(target).encode()).hexdigest()[:16]}")
    )
    inserted_root = str(import_root)
    add_import_root = inserted_root not in sys.path
    if add_import_root:
        sys.path.insert(0, inserted_root)
    try:
        if package_name:
            importlib.import_module(package_name)
        existing = sys.modules.get(module_name)
        existing_path = getattr(existing, "__file__", None)
        if existing is not None and existing_path is not None and Path(existing_path).resolve() == target:
            return existing, syntax_tree

        spec = importlib.util.spec_from_file_location(module_name, target)
        if spec is None or spec.loader is None:
            raise GenerationCommandError(f"could not load target module: {target}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as error:
            raise GenerationCommandError(f"could not import target module {target}: {error}") from error
        finally:
            if existing is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = existing
        return module, syntax_tree
    finally:
        if add_import_root:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with suppress(ValueError):
                    sys.path.remove(inserted_root)


def _package_context(target: Path) -> tuple[str | None, Path]:
    package_parts: list[str] = []
    current = target.parent
    while (current / "__init__.py").is_file():
        package_parts.insert(0, current.name)
        current = current.parent
    return (".".join(package_parts) or None), current


def _unique_steps(features: Sequence[Feature]) -> list[Step]:
    found: dict[tuple[str, str], Step] = {}
    for feature in features:
        for scenario in feature.pickles:
            for step in scenario.steps:
                step_type = _normalized_step_type(step)
                found.setdefault((step_type.value, step.text), step)
    return sorted(found.values(), key=lambda step: (_normalized_step_type(step).value, step.text))


def _normalized_step_type(step: Step) -> StepType:
    if isinstance(step.type, StepType):
        return step.type
    raw_type = str(step.type or "").casefold()
    keyword = step.keyword.strip().casefold()
    if raw_type in {"context", "given"} or keyword == "given":
        return StepType.context
    if raw_type in {"action", "when"} or keyword == "when":
        return StepType.action
    if raw_type in {"outcome", "then"} or keyword == "then":
        return StepType.outcome
    return StepType.unknown


def _missing_steps(features: Sequence[Feature], module: ModuleType, target: Path) -> tuple[list[Step], Path, Path]:
    """Match steps with pytest's real fixture request and target module registry."""
    module_name = module.__name__
    prior_module = sys.modules.get(module_name)
    sys.modules[module_name] = module

    feature_paths = sorted({str(Path(feature.filename or feature.rel_filename).resolve()) for feature in features})
    root_directory, pytest_config = _pytest_context(target)
    feature_root = str(root_directory)
    test_module = _render_inspection_module(module_name, feature_paths, feature_root)
    inspector = _StepInspectionPlugin()
    captured_stdout = StringIO()
    captured_stderr = StringIO()
    try:
        with tempfile.TemporaryDirectory(prefix="pytest-cuke-generation-", dir=target.parent) as temporary_directory:
            test_path = Path(temporary_directory) / f"test_cuke_generation_{uuid4().hex}.py"
            test_path.write_text(test_module, encoding="utf-8", newline="")
            if pytest_config is None:
                pytest_config = Path(temporary_directory) / "pytest.ini"
                pytest_config.write_text("[pytest]\n", encoding="utf-8", newline="")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", PytestBDDStepDefinitionWarning)
                previous_directory = Path.cwd()
                try:
                    os.chdir(root_directory)
                    with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                        exit_code = pytest.main(
                            [
                                "--collect-only",
                                "-q",
                                "-q",
                                "--disable-warnings",
                                "--cuke-no-autoload",
                                "--cuke-allow-empty-scenarios",
                                "-p",
                                "no:cacheprovider",
                                "-c",
                                str(pytest_config),
                                "--rootdir",
                                str(root_directory),
                                "--confcutdir",
                                str(root_directory),
                                str(test_path),
                            ],
                            plugins=[inspector],
                        )
                finally:
                    os.chdir(previous_directory)
    finally:
        if prior_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior_module

    if inspector.error is not None:
        raise GenerationCommandError(inspector.error)
    if int(exit_code) != 0:
        diagnostic = "\n".join(
            output.strip() for output in (captured_stdout.getvalue(), captured_stderr.getvalue()) if output.strip()
        )
        message = (
            f"pytest could not collect the selected features with target module {target} (exit code {int(exit_code)})"
        )
        if diagnostic:
            message = f"{message}:\n{diagnostic}"
        raise GenerationCommandError(message)
    missing = sorted(inspector.missing.values(), key=lambda step: (_normalized_step_type(step).value, step.text))
    return missing, inspector.project_root or root_directory, inspector.features_base_dir or root_directory


def _pytest_context(target: Path) -> tuple[Path, Path | None]:
    """Find the target project's pytest configuration, ignoring shared temp-root config."""
    configuration_names = ("pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")
    temporary_root = Path(tempfile.gettempdir()).resolve()
    for directory in target.parents:
        if directory.resolve() == temporary_root:
            continue
        for name in configuration_names:
            config = directory / name
            if not config.is_file():
                continue
            if name == "pyproject.toml":
                content = config.read_text(encoding="utf-8", errors="ignore")
                if "[tool.pytest.ini_options]" not in content and "[tool.pytest]" not in content:
                    continue
            return directory, config
    return Path.cwd().resolve(), None


def _configured_features_base_dir(config: Any, project_root: Path) -> Path:
    features_base_dir = config.getoption("cuke_features_dir")
    if features_base_dir is None:
        features_base_dir = config.getini("cuke_features_dir") or project_root
    if callable(features_base_dir):
        features_base_dir = features_base_dir(config)
    path = Path(features_base_dir).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _render_inspection_module(module_name: str, feature_paths: Sequence[str], feature_root: str) -> str:
    """Create a temporary pytest module that exposes the target's steps and features."""
    return "\n".join(
        (
            "import importlib as _pytest_cuke_importlib",
            "from pytest_cuke import scenarios as _pytest_cuke_scenarios",
            f"_pytest_cuke_target = _pytest_cuke_importlib.import_module({module_name!r})",
            "globals().update({",
            "    name: value",
            "    for name, value in vars(_pytest_cuke_target).items()",
            "    if name == 'pytest_plugins'",
            "    or hasattr(value, '__pytest_cuke_step_definitions__')",
            "    or hasattr(value, '_pytestfixturefunction')",
            "})",
            f"test_scenarios_for_generation = _pytest_cuke_scenarios(*{tuple(feature_paths)!r}, ",
            "filter_=None, return_test_decorator=False, ",
            f"features_base_dir={feature_root!r})",
            "",
        )
    )


class _StepInspectionPlugin:
    """Inspect collected scenario items without entering pytest's call phase."""

    def __init__(self) -> None:
        self.missing: dict[tuple[str, str], Step] = {}
        self.error: str | None = None
        self.project_root: Path | None = None
        self.features_base_dir: Path | None = None

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: Session) -> None:
        self.project_root = Path(session.config.rootpath).resolve()
        self.features_base_dir = _configured_features_base_dir(session.config, self.project_root)
        for item in session.items:
            if not {"feature", "scenario"}.issubset(getattr(item, "fixturenames", ())):
                continue
            self._inspect_item(item)
            if self.error is not None:
                return

    def _inspect_item(self, item: Any) -> None:
        setup_state = item.session._setupstate
        setup_name = "setup" if PYTEST7 else "prepare"
        setup_attempted = False
        try:
            setup_attempted = True
            getattr(setup_state, setup_name)(item)
            request = item._request
            feature = cast("Feature", request.getfixturevalue("feature"))
            scenario = cast("Scenario", request.getfixturevalue("scenario"))
            for match in iter_step_definition_matches(request, feature, scenario, detect_ambiguity=True):
                if match.ambiguous:
                    step = match.step
                    raise GenerationCommandError(
                        f"ambiguous existing step definitions for {step.keyword.strip()} {step.text!r}; "
                        "remove or narrow one matching parser before generating"
                    )
                if not match.matched:
                    normalized_type = _normalized_step_type(match.step)
                    self.missing.setdefault((normalized_type.value, match.step.text), match.step)
        except Exception as error:
            self.error = (
                str(error)
                if isinstance(error, (GenerationCommandError, StepDefinitionInspectionError))
                else (f"could not inspect pytest fixtures for {item.nodeid}: {error}")
            )
        finally:
            if setup_attempted:
                self._teardown_item(item)

    def _teardown_item(self, item: Any) -> None:
        setup_state = item.session._setupstate
        try:
            teardown_exact = cast("Any", setup_state.teardown_exact)
            if PYTEST7:
                teardown_exact(None)
            else:
                teardown_exact(item, None)
        except Exception as error:
            if self.error is None:
                self.error = f"could not release pytest fixtures for {item.nodeid}: {error}"
            else:
                self.error += f" (fixture teardown also failed: {error})"


def _missing_scenarios(
    features: Sequence[Feature],
    module: ModuleType,
    target: Path,
    project_root: Path,
    features_base_dir: Path,
) -> list[tuple[Feature, Scenario]]:
    bindings = _scenario_bindings(module)
    result: list[tuple[Feature, Scenario]] = []
    for feature in features:
        for scenario in feature.pickles:
            matched = [
                binding
                for binding in bindings
                if _binding_matches(binding, feature, scenario, target, project_root, features_base_dir)
            ]
            if len(matched) > 1:
                raise GenerationCommandError(
                    f"multiple existing scenario bindings match {feature.rel_filename!r} / {scenario.name!r}; "
                    "remove duplicate bindings before generating"
                )
            if not matched:
                result.append((feature, scenario))
    return result


def _scenario_bindings(module: ModuleType) -> list[tuple[tuple[object, ...], dict[str, object]]]:
    bindings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    visited: set[int] = set()
    for value in vars(module).values():
        if id(value) in visited:
            continue
        visited.add(id(value))
        marks = getattr(value, "pytestmark", ())
        if not isinstance(marks, (tuple, list)):
            marks = (marks,)
        for mark in marks:
            if getattr(mark, "name", None) == "scenarios":
                bindings.append((tuple(getattr(mark, "args", ())), dict(getattr(mark, "kwargs", {}))))
    return bindings


def _binding_matches(
    binding: tuple[tuple[object, ...], dict[str, object]],
    feature: Feature,
    scenario: Scenario,
    target: Path,
    project_root: Path,
    features_base_dir: Path,
) -> bool:
    paths, options = binding
    selector = options.get("filter_")
    if selector is not None and not isinstance(selector, str):
        if callable(selector):
            raise GenerationCommandError(
                f"cannot safely compare callable scenario filter for {feature.rel_filename!r}; "
                "use a literal filter or remove --bind-scenarios"
            )
        return False
    if isinstance(selector, str) and selector != scenario.name:
        return False
    if not paths:
        return True

    return _binding_matches_feature_paths(paths, options, feature, target, project_root, features_base_dir)


def _binding_matches_feature_paths(
    paths: Sequence[object],
    options: dict[str, object],
    feature: Feature,
    target: Path,
    project_root: Path,
    features_base_dir: Path,
) -> bool:

    feature_path = Path(feature.filename or feature.rel_filename).expanduser().resolve()
    base_value = options.get("features_base_dir")
    if callable(base_value):
        raise GenerationCommandError(
            f"cannot safely compare callable scenario feature base in {target}; "
            "use a literal features_base_dir or remove --bind-scenarios"
        )
    base = Path(str(base_value)).expanduser() if base_value is not None else features_base_dir
    if not base.is_absolute():
        base = project_root / base
    base = base.resolve()
    for raw_path in paths:
        path_text = os.fspath(raw_path) if isinstance(raw_path, os.PathLike) else str(raw_path)
        if not _has_windows_drive_prefix(path_text):
            parsed = urlsplit(path_text)
            if parsed.scheme and parsed.scheme != "file":
                continue
            if parsed.scheme == "file":
                path_text = _file_uri_path(parsed)
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = base / path
        resolved_path = path.resolve()
        if glob.has_magic(path_text):
            pattern_path = Path(path_text)
            if pattern_path.is_absolute():
                candidates = pattern_path.parent.glob(pattern_path.name)
            else:
                candidates = base.glob(path_text)
            if any(candidate.resolve() == feature_path for candidate in candidates):
                return True
        elif resolved_path.is_dir():
            try:
                feature_path.relative_to(resolved_path)
                return True
            except ValueError:
                pass
        elif feature_path == resolved_path:
            return True

    # A custom locator binding cannot be proven equivalent from public marker data.
    if options.get("locators"):
        raise GenerationCommandError(
            f"cannot safely compare custom scenario locator in {target}; "
            "remove --bind-scenarios or use an explicit feature path"
        )
    return False


def _has_windows_drive_prefix(path_text: str) -> bool:
    """Distinguish Windows drive paths from URL schemes on every host OS."""
    return len(path_text) >= 2 and path_text[0].isalpha() and path_text[1] == ":"


def _file_uri_path(parsed: SplitResult) -> str:
    """Decode a local file URI into the current platform's path syntax."""
    path = url2pathname(parsed.path)
    if parsed.netloc and parsed.netloc.casefold() != "localhost":
        path_without_root = path.lstrip("/\\")
        return f"//{parsed.netloc}{os.sep}{path_without_root}"
    return path


def _render_additions(
    steps: Sequence[Step],
    scenarios: Sequence[tuple[Feature, Scenario]],
    module: ModuleType | None,
    syntax_tree: ast.Module | None,
    *,
    target: Path | None = None,
) -> str:
    if not steps and not scenarios:
        return ""

    namespace = vars(module) if module is not None else {}
    decorator_names = {_decorator_name_for_step(step) for step in steps}
    if scenarios:
        decorator_names.add("scenario")
    expressions, imports = _existing_public_expressions(decorator_names, namespace, syntax_tree)
    for decorator_name in sorted(decorator_names):
        if decorator_name not in expressions:
            alias = _available_name(namespace, f"_pytest_cuke_{decorator_name}", decorator_name)
            expressions[decorator_name] = alias
            imports.add(f"{decorator_name} as {alias}" if alias != decorator_name else decorator_name)

    path_expression: str | None = None
    path_import: str | None = None
    if scenarios:
        path_expression, path_import = _path_expression(namespace, syntax_tree)
        if path_import:
            imports.add(path_import)

    lines: list[str] = []
    if imports:
        public_imports = sorted(item for item in imports if not item.startswith("from pathlib import "))
        pathlib_imports = sorted(item for item in imports if item.startswith("from pathlib import "))
        if public_imports:
            lines.append(f"from pytest_cuke import {', '.join(public_imports)}")
        lines.extend(pathlib_imports)
        lines.append("")

    used_names = set(namespace)
    generated: set[str] = set()
    for step in steps:
        base_name = "step_" + make_python_name(step.text)
        function_name = _unique_function_name(base_name, used_names | generated)
        generated.add(function_name)
        decorator = expressions[_decorator_name_for_step(step)]
        lines.extend(
            (
                f"@{decorator}({step.text!a})",
                f"def {function_name}():",
                '    """Implement the matching feature step."""',
                f"    raise NotImplementedError({'Implement: ' + step.text!a})",
                "",
            )
        )

    for feature, scenario in scenarios:
        if target is None or path_expression is None:
            continue
        relative_path = _relative_feature_path(feature, target)
        feature_expression = f"{path_expression}(__file__).parent / {relative_path!a}"
        base_name = "test_" + make_python_name(scenario.name)
        function_name = _unique_function_name(base_name, used_names | generated)
        generated.add(function_name)
        decorator = expressions["scenario"]
        lines.extend(
            (
                f"@{decorator}({feature_expression}, {scenario.name!a})",
                f"def {function_name}():",
                f"    {make_python_docstring(scenario.name)}",
                "    pass",
                "",
            )
        )

    return "\n".join(lines).rstrip() + "\n"


def _decorator_name_for_step(step: Step) -> str:
    step_type = _normalized_step_type(step)
    return STEP_TYPE_TO_STEP_METHOD_NAME[step_type]


def _existing_public_expressions(
    required: Iterable[str], namespace: dict[str, Any], syntax_tree: ast.Module | None
) -> tuple[dict[str, str], set[str]]:
    expressions: dict[str, str] = {}
    imports: set[str] = set()
    if syntax_tree is None:
        return expressions, imports

    public_module = pytest_cuke
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "pytest_cuke":
            for alias in node.names:
                if alias.name == "*":
                    for name in required:
                        public_value = getattr(public_module, name, None)
                        if namespace.get(name) is public_value:
                            expressions.setdefault(name, name)
                    continue
                if alias.name in required:
                    local_name = alias.asname or alias.name
                    if namespace.get(local_name) is getattr(public_module, alias.name, None):
                        expressions.setdefault(alias.name, local_name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != "pytest_cuke":
                    continue
                local_name = alias.asname or alias.name
                if namespace.get(local_name) is public_module:
                    for name in required:
                        if hasattr(public_module, name):
                            expressions.setdefault(name, f"{local_name}.{name}")
    return expressions, imports


def _path_expression(namespace: dict[str, Any], syntax_tree: ast.Module | None) -> tuple[str, str | None]:
    if syntax_tree is not None:
        for node in ast.walk(syntax_tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "pathlib":
                for alias in node.names:
                    if alias.name == "Path":
                        local_name = alias.asname or alias.name
                        if namespace.get(local_name) is Path:
                            return local_name, None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pathlib":
                        local_name = alias.asname or alias.name
                        module = namespace.get(local_name)
                        if module is not None and getattr(module, "Path", None) is Path:
                            return f"{local_name}.Path", None

    path_alias = _available_name(namespace, "_pytest_cuke_Path", "Path")
    import_statement = (
        f"from pathlib import Path as {path_alias}" if path_alias != "Path" else "from pathlib import Path"
    )
    return path_alias, import_statement


def _available_name(namespace: dict[str, Any], preferred: str, plain: str) -> str:
    if plain not in namespace:
        return plain
    if preferred not in namespace:
        return preferred
    suffix = 2
    while f"{preferred}_{suffix}" in namespace:
        suffix += 1
    return f"{preferred}_{suffix}"


def _unique_function_name(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    suffix = 2
    while f"{base}_{suffix}" in used:
        suffix += 1
    return f"{base}_{suffix}"


def _relative_feature_path(feature: Feature, target: Path) -> str:
    feature_path = Path(feature.filename or feature.rel_filename).expanduser().resolve()
    try:
        return Path(os.path.relpath(feature_path, target.parent)).as_posix()
    except ValueError as error:
        raise GenerationCommandError(
            f"feature {feature_path} and target {target} must be on the same volume for a portable binding"
        ) from error


def _report_result(
    result: SourceEditResult,
    target: Path,
    step_count: int,
    scenario_count: int,
    preview: bool,
) -> None:
    if preview:
        if result.diff:
            print(result.diff, end="")
        else:
            print("No changes required.")
    elif result.changed:
        print(f"Updated {target}: added {step_count} step definition(s) and {scenario_count} scenario binding(s).")
    else:
        print(f"No changes required in {target}.")


__all__ = ["configure_generate_steps_parser", "run_generate_steps"]
