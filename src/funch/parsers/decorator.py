import ast
from typing import Iterator


def yield_decorated(
    code: str, module: str, name: str, with_args: bool = False
) -> Iterator[tuple[str, str]]:
    """Yields names of functions decorated with `@module.name` in `code`.

    Args:
        code: Source code to parse
        module: Module name in decorator (e.g. 'funsearch')
        name: Decorator name (e.g. 'run')
        with_args: If True, yields (function_name, arg_name) tuples for decorators with arguments

    Yields:
        (function_name, function_name) or (function_name, arg_name) tuples if with_args=True
    """
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                attribute = None
                arg = None

                # Handle @module.name or @module.name(arg)
                if isinstance(decorator, ast.Attribute):
                    attribute = decorator
                elif isinstance(decorator, ast.Call):
                    if not (isinstance(decorator.func, ast.Attribute)):
                        continue
                    attribute = decorator.func
                    # Get first argument if present
                    if (
                        decorator.args
                        and isinstance(decorator.args[0], ast.Constant)
                        and isinstance(decorator.args[0].value, str)
                    ):
                        arg = decorator.args[0].value
                    elif decorator.args and isinstance(decorator.args[0], ast.Name):
                        arg = decorator.args[0].id

                if (
                    attribute is not None
                    and isinstance(attribute.value, ast.Name)
                    and attribute.value.id == module
                    and attribute.attr == name
                ):
                    if with_args:
                        if arg is None:
                            raise ValueError(
                                f"Decorator @{module}.{name} requires an argument "
                                f"for function {node.name}"
                            )
                        yield node.name, arg
                    else:
                        yield node.name, node.name
