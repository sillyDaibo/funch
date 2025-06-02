from typing import Optional, Tuple, Any
import os
from pathlib import Path
from funch.evaluator.from_template import FromTemplate
from funch.llm import LLMClient
from funch.parsers.function_body import parse_function_body
from funch.storage.item_storage.storage import ItemStorage
from funch.storage.string_database.plain_database import PlainStringDatabase

class BasicWorkflow:
    def __init__(
        self, 
        template_path: str, 
        llm_model: str = "deepseek-chat",
        temperature: float = 0.7,
        tag: Optional[str] = None,
        score_input: Any = None,
        storage: Optional[ItemStorage] = None
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
        self.prompt_header = ("Please generate an improved version of this Python function. "
                            "Keep the exact same function signature and docstring. "
                            "Only respond with the full function implementation.")

    def generate(self, batch_size: int = 1) -> Tuple[str, bool, float]:
        """Generate, validate and score function versions.
        
        Args:
            batch_size: Number of candidates to generate and pick best from
            
        Returns:
            Tuple of (best_function_body, is_valid, highest_score)
        """
        best_body = ""
        best_score = float("-inf")
        best_is_valid = False
        
        if batch_size > 1:
            print(f"Running batch of {batch_size} generations...")
        
        for i in range(batch_size):
            # Build the prompt
            prompt = (
                f"{self.prompt_header}\n\n"
                f"Current implementation:\n"
                f"{self.template_processor.get_function_heading()}\n"
                f"{self.template_processor.get_function_body()}"
            )
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse function body from response
            try:
                new_body = parse_function_body(response, self.function_name)
            except Exception as e:
                print(f"Failed to parse function body: {e}")
                continue

            # Validate and score
            is_valid = self.validity_checker.is_valid(new_body)
            score = float("-inf")
            if is_valid and self.score_evaluator:
                score = self.score_evaluator(new_body)
                if batch_size > 1:
                    print(f"  Candidate #{i+1} score: {score:.2f} "
                          f"{'✅' if is_valid else '❌'}")

            # Track best candidate
            if score > best_score:
                best_body = new_body
                best_score = score
                best_is_valid = is_valid
        
        if batch_size > 1 and best_score > float("-inf"):
            print(f"Selected best candidate with score: {best_score:.2f}")
        
        return best_body, best_is_valid, best_score
