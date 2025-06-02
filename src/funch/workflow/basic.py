from typing import Optional, Tuple
import os
from pathlib import Path
from funch.evaluator.from_template import FromTemplate
from funch.llm import LLMClient
from funch.parsers.function_body import parse_function_body

from typing import Any

class BasicWorkflow:
    def __init__(self, template_path: str, llm_model: str = "deepseek-chat"):
        """Initialize workflow with template and LLM settings."""
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r') as f:
            self.template = f.read()
        
        self.template_processor = FromTemplate(self.template)
        self.llm = LLMClient(model=llm_model)
        self.function_name = self.template_processor.get_function_name()
        self.validity_checker = self.template_processor.build_validity_checker()
        self.score_evaluator = None
        self.prompt_header = ("Please generate an improved version of this Python function. "
                            "Keep the exact same function signature and docstring. "
                            "Only respond with the full function implementation.")

    def set_score_evaluator(self, tag: str, input: Any):
        """Configure scoring for the workflow."""
        self.score_evaluator = self.template_processor.build_score_evaluator(tag, input)

    def generate(self) -> Tuple[str, bool, Optional[float]]:
        """Generate, validate and score a new function version."""
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
            return response, False, None

        # Validate and score
        is_valid = self.validity_checker.is_valid(new_body)
        score = None
        if is_valid and self.score_evaluator:
            score = self.score_evaluator(new_body)

        return new_body, is_valid, score
