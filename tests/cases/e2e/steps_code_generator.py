import ast

from pytest_bdd import then


def _generated_python_module(pytest_result) -> ast.Module:
    stdout = pytest_result.stdout.str()
    code_lines = [
        line for line in stdout.splitlines() if line.startswith(("from ", "import ", "@", "def ", "    ", "raise "))
    ]
    code = "\n".join(code_lines)
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        message = f"Generated output is not valid Python:\n{stdout}"
        raise AssertionError(message) from exc


def _step_decorators(module: ast.Module) -> list[tuple[str, str]]:
    decorators: list[tuple[str, str]] = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name):
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            decorators.append((decorator.func.id, str(decorator.args[0].value)))
    return decorators


@then("generated Python code matches oracle:")
def generated_python_code_matches_oracle(pytest_result, step):
    actual = _generated_python_module(pytest_result)
    expected = ast.parse(step.argument.doc_string.content)

    assert sorted(_step_decorators(actual)) == sorted(_step_decorators(expected))


@then("generated Python code defines functions:")
def generated_python_code_defines_functions(pytest_result, step):
    module = _generated_python_module(pytest_result)
    expected = [row.cells[0].value for row in step.argument.data_table.rows[1:]]
    actual = [node.name for node in module.body if isinstance(node, ast.FunctionDef)]
    assert actual == expected


@then("Generated code is printed to stdout")
def generated_code_is_printed(pytest_result):
    assert pytest_result.ret == 0
    assert _generated_python_module(pytest_result).body
