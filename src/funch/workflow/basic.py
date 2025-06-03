from typing import Optional, Tuple, Any, List
import os
import logging
import asyncio
from enum import IntEnum
from pathlib import Path

from funch.evaluator.from_template import FromTemplate
from funch.llm import LLMClient
from funch.parsers.function_body import parse_function_body
from funch.storage.item_storage.storage import ItemStorage
from funch.storage.string_database.plain_database import PlainStringDatabase
from funch.storage import SQLiteStringDatabase


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
        verbosity: int = Verbosity.BASIC,
        logger: Optional[BasicLogger] = None
    ):
        """Initialize workflow with template and LLM settings.
        
        Args:
            template_path: Path to template file
            llm_model: Name of LLM model to use
            tag: Tag for scoring function (None uses first found)
            score_input: Input to pass to scoring function
            logger: Optional BasicLogger instance to use (will create one if None)
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
        if storage is None:
            db = SQLiteStringDatabase(":memory:")
            self.storage = ItemStorage(db)
        else:
            self.storage = storage
        self.logger = logger if logger is not None else BasicLogger(verbosity)
        self.prompt_header = ("Please generate an improved version of this Python function. "
                            "You should be creative and willing to try new methods. "
                            "Keep the exact same function signature and docstring. "
                            "Only respond with the full function implementation.")

    def _build_prompt(self, candidate_num: int) -> str:
        """Build the prompt for the LLM including best previous examples."""
        # Get all available functions sorted by score (highest last)
        available_funcs = [item for item in self.storage.items() if hasattr(item, 'func')]
        sorted_funcs = sorted(
            available_funcs,
            key=lambda x: getattr(x, 'score', float('-inf'))
        )  # Sort ascending so highest score is last
        
        # Take at most 3 functions, keeping ordering (so highest score remains last)
        top_funcs = sorted_funcs[-3:]

        examples = ""
        for example_num, item in enumerate(top_funcs):
            examples += (
                f"\n\nExample {'ABC'[example_num] if len(top_funcs) == 3 else example_num+1} "
                f"(Score: {getattr(item, 'score', 0):.2f}):\n"
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

    async def _generate_batch(self, prompts: List[str]) -> List[tuple[str, bool, float]]:
        """Generate and process a batch of candidates asynchronously."""
        responses = await asyncio.gather(*[
            self.llm.invoke_async(prompt) for prompt in prompts
        ])
        return [self._process_candidate(response) for response in responses]

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
                self.logger.info(f"--- Iteration {iteration + 1}/{iterations} ---")
        
            # Build all prompts first
            prompts = [self._build_prompt(candidate_num) for candidate_num in range(batch_size)]
            
            # Process batch async
            batch_results = asyncio.run(self._generate_batch(prompts))
            
            for candidate_num, (new_body, is_valid, score) in enumerate(batch_results):
                
                total_generated += 1
                if is_valid:
                    total_valid += 1
                else:
                    total_failed += 1

                _update_progress()
                
                if batch_size > 1 and self.logger.verbosity >= Verbosity.DETAILED:
                    self.logger.info(f"Candidate #{candidate_num+1} score: {score:.2f} "
                                  f"{'✅' if is_valid else '❌'}")
                                  

                # Treat -inf scores as invalid
                effective_valid = is_valid and score != float('-inf')
                if score > best_score:
                    best_body, best_score, best_is_valid = new_body, score, effective_valid
                    storage_item = self.storage.new()
                    storage_item.func = best_body
                    storage_item.score = best_score
                    storage_item.valid = best_is_valid

                    if score > overall_best_score:
                        overall_best_body, overall_best_score = best_body, best_score
                        overall_best_valid = best_is_valid
                        self.logger.debug(f"New best score: {best_score:.2f}")
            
        if self.logger.verbosity < Verbosity.DEBUG:
            print()  # New line after progress
            
        self.logger.info(f"\n🎉 Optimization Complete! "
                       f"(Total: {total_generated} | "
                       f"Valid: {total_valid/total_generated:.0%} | "
                       f"Best: {overall_best_score:.2f})")
        
        if total_valid < total_generated:
            self.logger.warning(
                f"⚠️  Some generated functions were invalid. Check 'sandbox_errors.log' "
                f"for details about the failures."
            )
        return overall_best_body, overall_best_valid, overall_best_score
