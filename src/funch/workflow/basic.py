from typing import Optional, Tuple, Any
import os
import logging
from enum import IntEnum
from pathlib import Path

from funch.evaluator.from_template import FromTemplate
from funch.llm import LLMClient
from funch.parsers.function_body import parse_function_body
from funch.storage.item_storage.storage import ItemStorage
from funch.storage.string_database.plain_database import PlainStringDatabase


class Verbosity(IntEnum):
    SILENT = 0
    BASIC = 1
    DETAILED = 2
    DEBUG = 3

class BasicLogger:
    def __init__(self, verbosity=Verbosity.BASIC):
        self.verbosity = verbosity
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        if verbosity >= Verbosity.DEBUG:
            ch.setLevel(logging.DEBUG)
        elif verbosity >= Verbosity.DETAILED:
            ch.setLevel(logging.INFO)
        else:
            ch.setLevel(logging.WARNING)
            
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def debug(self, msg):
        if self.verbosity >= Verbosity.DEBUG:
            self.logger.debug(msg)

    def info(self, msg):
        if self.verbosity >= Verbosity.DETAILED:
            self.logger.info(msg)

    def warning(self, msg):
        if self.verbosity >= Verbosity.BASIC:
            self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

class BasicWorkflow:
    def __init__(
        self,
        template_path: str,
        llm_model: str = "deepseek-chat",
        temperature: float = 0.7,
        tag: Optional[str] = None,
        score_input: Any = None,
        storage: Optional[ItemStorage] = None,
        verbosity: int = Verbosity.BASIC
    ):
        """Initialize workflow with template and LLM settings.
        
        Args:
            template_path: Path to template file
            llm_model: Name of LLM model to use
            tag: Tag for scoring function (None uses first found)
            score_input: Input to pass to scoring function
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r') as f:
            self.template = f.read()
        
        self.template_processor = FromTemplate(self.template)
        self.llm = LLMClient(model=llm_model, temperature=temperature)
        self.function_name = self.template_processor.get_function_name()
        self.validity_checker = self.template_processor.build_validity_checker()
        self.score_evaluator = self.template_processor.build_score_evaluator(
            tag, score_input
        )
        self.storage = storage if storage is not None else ItemStorage(PlainStringDatabase())
        self.logger = BasicLogger(verbosity)
        self.prompt_header = ("Please generate an improved version of this Python function. "
                            "You should be creative and willing to try new methods. "
                            "Keep the exact same function signature and docstring. "
                            "Only respond with the full function implementation.")

    def _build_prompt(self, candidate_num: int) -> str:
        """Build the prompt for the LLM including best previous examples."""
        top_funcs = sorted(
            [item for item in self.storage.items() if hasattr(item, 'func')],
            key=lambda x: getattr(x, 'score', float('-inf')),
            reverse=True
        )[:3]

        examples = ""
        for example_num, item in enumerate(top_funcs):
            examples += (
                f"\n\nExample {example_num+1} (Score: {getattr(item, 'score', 0):.2f}):\n"
                f"{self.template_processor.get_function_heading()}\n"
                f"{getattr(item, 'func', '')}"
            )

        return (
            f"{self.prompt_header}\n"
            f"Current implementation:\n"
            f"{self.template_processor.get_function_heading()}\n"
            f"{self.template_processor.get_function_body()}\n"
            f"\nPrevious best examples:{examples}"
        )

    def _process_candidate(self, response: str) -> Tuple[str, bool, float]:
        """Process a single candidate response from LLM."""
        try:
            new_body = parse_function_body(response, self.function_name)
        except Exception as e:
            print(f"Failed to parse function body: {e}")
            return "", False, float("-inf")
            
        is_valid = self.validity_checker.is_valid(new_body)
        score = float("-inf")
        if is_valid and self.score_evaluator:
            score = self.score_evaluator(new_body)
        return new_body, is_valid, score

    def generate(self, batch_size: int = 1, iterations: int = 1) -> Tuple[str, bool, float]:
        """Generate, validate and score function versions.
        
        Args:
            batch_size: Number of candidates to generate per iteration
            iterations: Number of iterations to run
            
        Returns:
            Tuple of (best_function_body, is_valid, highest_score)
        """
        total_generated = 0
        total_valid = 0
        total_failed = 0
        overall_best_body = ""
        overall_best_score = float("-inf")
        overall_best_valid = False
        
        def _update_progress():
            if self.logger.verbosity < Verbosity.DEBUG:
                print(f"\r🚀 Process: {iteration+1}/{iterations} iters | "
                      f"{candidate_num+1}/{batch_size} batch | "
                      f"{total_generated} total | "
                      f"Best: {overall_best_score:.2f}", end="", flush=True)
        
        for iteration in range(iterations):
            best_body = ""
            best_score = float("-inf") 
            best_is_valid = False
            
            if self.logger.verbosity >= Verbosity.DETAILED:
                self.logger.info(f"\n--- Iteration {iteration + 1}/{iterations} ---")
        
            for candidate_num in range(batch_size):
                prompt = self._build_prompt(candidate_num)
                
                response = self.llm.invoke(prompt)
                new_body, is_valid, score = self._process_candidate(response)
                
                total_generated += 1
                if is_valid:
                    total_valid += 1
                else:
                    total_failed += 1

                _update_progress()
                
                if batch_size > 1 and self.logger.verbosity >= Verbosity.DETAILED:
                    self.logger.info(f"Candidate #{candidate_num+1} score: {score:.2f} "
                                  f"{'✅' if is_valid else '❌'}")
                                  

                if score > best_score:
                    best_body, best_score, best_is_valid = new_body, score, is_valid
                    storage_item = self.storage.new()
                    storage_item.func = best_body
                    storage_item.score = best_score
                    storage_item.valid = best_is_valid

                    if score > overall_best_score:
                        overall_best_body, overall_best_score = best_body, best_score
                        overall_best_valid = best_is_valid
                        self.logger.debug(f"New best score: {best_score:.2f}")
            
        self.logger.info(
            f"\n--- Process Summary ---\n"
            f"Total candidates generated: {total_generated}\n"
            f"Valid candidates: {total_valid} ({total_valid/total_generated:.1%})\n"
            f"Failed candidates: {total_failed} ({total_failed/total_generated:.1%})\n"
            f"Best score achieved: {overall_best_score:.2f}\n"
        )
        return overall_best_body, overall_best_valid, overall_best_score
