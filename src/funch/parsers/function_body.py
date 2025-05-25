import re
import ast
from typing import Any


INDENT_WIDTH = 4


def parse_function_body(text_and_code: str, function_name_pattern: str) -> str:
    """
    Extract the body of a function from a given text containing code.

    Args:
        text_and_code (str): The text that may contain a code block.
        function_name_pattern (str): The pattern of the function name to search for.

    Returns:
        str: The extracted function body, trimmed and properly indented.
    """
    if not text_and_code.strip():
        return ""

    code_block_pattern = r"```(python|py)\n(.*?)```"
    match = re.search(code_block_pattern, text_and_code, re.DOTALL)
    if match:
        code = match.group(2)
    else:
        code = text_and_code

    lines = code.splitlines()
    last_match_index = -1
    function_pattern = re.compile(r"def (" + function_name_pattern + r")\(.*?:")
    for i, line in enumerate(lines):
        if function_pattern.match(line):
            last_match_index = i
    if last_match_index != -1:
        function_body = "\n".join(lines[last_match_index + 1 :])
    else:
        function_body = code

    if last_match_index == -1:
        # If purely function body
        indent = INDENT_WIDTH
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                break

        if indent != INDENT_WIDTH:
            indent_diff = INDENT_WIDTH - indent
            adjusted_lines = []
            for line in lines:
                if line.strip():
                    adjusted_lines.append(" " * indent_diff + line)
                else:
                    adjusted_lines.append(line)
            function_body = "\n".join(adjusted_lines)

    # 去除开头的空行
    function_body = " " * INDENT_WIDTH + function_body.lstrip()
    trimmed_function_body = _trim_function_body(function_body, INDENT_WIDTH)

    return trimmed_function_body


class _FunctionLineVisitor(ast.NodeVisitor):
    """Visitor that finds the last line number of a function with a given name."""

    def __init__(self, target_function_name: str) -> None:
        self._target_function_name: str = target_function_name
        self._function_end_line: int | None = None

    def visit_FunctionDef(self, node: Any) -> None:  # pylint: disable=invalid-name
        """Collects the end line number of the target function."""
        if node.name == self._target_function_name:
            self._function_end_line = node.end_lineno
        self.generic_visit(node)

    @property
    def function_end_line(self) -> int:
        """Line number of the final line of function `target_function_name`."""
        assert self._function_end_line is not None  # Check internal correctness.
        return self._function_end_line


def _trim_function_body(func_body: str, indent_width=4) -> str:
    """Extracts the body of the generated function, trimming anything after it."""
    if not func_body.strip():
        return " " * indent_width + "pass"
    code = f"def fake_function_header():\n{func_body}"
    tree = None
    # We keep trying and deleting code from the end until the parser succeeds.
    while tree is None:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            assert e.lineno
            code = "\n".join(code.splitlines()[: e.lineno - 1])
    if not code:
        # Nothing could be saved from `generated_code`
        return ""

    visitor = _FunctionLineVisitor("fake_function_header")
    visitor.visit(tree)
    body_lines = code.splitlines()[1 : visitor.function_end_line]
    return "\n".join(body_lines) + "\n\n"
