from funch.parsers import yield_decorated, parse_program
from .interface import ValidityChecker, ScoreEvaluator

import copy
import signal
import ast
import traceback

from typing import Any, Callable, Dict


class FromTemplate:
    ######################################
    #            Initialise              #
    ######################################
    def __init__(self, template: str):
        self.raw_template = template
        self.program = parse_program(template)
        self.func_to_evolve = self.__parse_func_to_evolve()

    def __parse_func_to_evolve(self):
        decorators = list(
            yield_decorated(
                self.raw_template, module="funch", name="evolve", with_args=False
            )
        )
        if len(decorators) != 1:
            raise ValueError(
                f"Expected exactly 1 function decorated with `@funch.evolve`, Found {len(decorators)}"
            )
        return decorators[0][0]

    ######################################
    #             Getters                #
    ######################################
    def get_function_name(self) -> str:
        return self.func_to_evolve

    def get_function_heading(self) -> str:
        return self.program.get_function(self.func_to_evolve).header().strip()

    def get_function_body(self) -> str:
        return self.program.get_function(self.func_to_evolve).body

    ######################################
    #          ValidityChecker           #
    ######################################
    def build_validity_checker(self, timeout_seconds=30) -> ValidityChecker:
        validate_funcs = [
            name
            for name, _ in yield_decorated(
                self.raw_template, module="funch", name="validate", with_args=False
            )
        ]
        if not validate_funcs:
            print(
                "Warning: no validate function found, is_valid will always return True"
            )

        def f(function_body: str) -> bool:
            program = self.__replace_body(function_body)
            for validate_func_name in validate_funcs:
                _, success = self.__sandbox(
                    program, validate_func_name, None, timeout_seconds
                )
                if not success:
                    return False
            return True

        return self.__ValidityChecker(f)

    class __ValidityChecker(ValidityChecker):
        def __init__(self, f: Callable[[str], bool]):
            self.f = f

        def is_valid(self, function_body: str) -> bool:
            return self.f(function_body)

    ######################################
    #          Score Evaluator           #
    ######################################
    def build_score_evaluator(
        self,
        tag: str,
        input: Any,
        timeout_seconds=30,
        failure_score: float = float("-inf"),
        complain=False,
    ) -> ScoreEvaluator:
        raw_funcs = {
            tag: name
            for name, tag in yield_decorated(
                self.raw_template, module="funch", name="run", with_args=False
            )
        }
        if tag not in raw_funcs:
            raise ValueError(f"No function decorated with @funch.run({tag}) found")
        raw_func = raw_funcs[tag]

        def f(function_body: str) -> Any:
            program = self.__replace_body(function_body)
            output, success = self.__sandbox(program, raw_func, input, timeout_seconds)
            if not success:
                if complain:
                    raise RuntimeError("evaluator failed to run")
                else:
                    return None
            return output

        g = self.__get_score_func(tag)
        return self.__ScoreEvaluator(f, g, failure_score)

    def __get_score_func(self, tag: str) -> Callable[[Any], float]:
        score_funcs = {
            tag: name
            for name, tag in yield_decorated(
                self.raw_template, module="funch", name="score", with_args=True
            )
        }
        if tag not in score_funcs:
            return lambda x: x

        try:
            namespace: Dict[Any, Any] = {}
            parsed_code = ast.parse(str(self.program))
            compiled_code = compile(parsed_code, filename="<ast>", mode="exec")
            exec(compiled_code, namespace)
        except Exception as e:
            raise ValueError(f"Score Evaluator didn't compile correctly {e}")
        return namespace[score_funcs[tag]]

    class __ScoreEvaluator(ScoreEvaluator):
        def __init__(
            self,
            f: Callable[[str], Any],
            g: Callable[[Any], float],
            failure_score: float,
        ):
            self.f = f
            self.g = g
            self.failure_score = failure_score

        def raw_output(self, function_body: str) -> Any:
            return self.f(function_body)

        def output_to_score(self, output: Any) -> float:
            return self.g(output) if output is not None else self.failure_score

    ######################################
    #              Common                #
    ######################################
    def __replace_body(self, function_body: str) -> str:
        program = copy.deepcopy(self.program)
        program.get_function(self.func_to_evolve).body = function_body
        return str(program)

    def __sandbox(
        self, program: str, function_to_run: str, test_input: Any, timeout_seconds: int
    ) -> tuple[Any, bool]:
        try:
            namespace: Dict[Any, Any] = {}
            parsed_code = ast.parse(program)
            compiled_code = compile(parsed_code, filename="<ast>", mode="exec")
            exec(compiled_code, namespace)

            def timeout_handler(*_):
                raise RuntimeError(
                    f"Time Out! Expected to finish in {timeout_seconds} seconds, stopping now..."
                )

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            if test_input is None:
                res = namespace[function_to_run]()
            else:
                res = namespace[function_to_run](test_input)
            signal.alarm(0)
            return res, True
        except Exception as e:
            error_msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            print(f"Error in Sandbox:\n{error_msg}")
            return None, False
