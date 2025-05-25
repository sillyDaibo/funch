from abc import ABC, abstractmethod

from typing import Any


class ValidityChecker(ABC):
    @abstractmethod
    def is_valid(self, function_body: str) -> bool:
        pass

    def __call__(self, function_body: str) -> bool:
        return self.is_valid(function_body)


class ScoreEvaluator(ABC):
    def score(self, function_body: str) -> float:
        return self.output_to_score(self.raw_output(function_body))

    @abstractmethod
    def raw_output(self, function_body: str) -> Any:
        return self.score(function_body)

    def output_to_score(self, output: Any) -> float:
        return output

    def __call__(self, function_body: str) -> float:
        return self.score(function_body)
