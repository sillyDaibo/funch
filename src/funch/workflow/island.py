from typing import Optional, Any, Tuple, List
from pathlib import Path

from funch.storage.item_storage.storage import ItemStorage
from funch.storage.item_storage.split_storage import split_item_storage
from funch.storage.string_database.sqlite_database import SQLiteStringDatabase

from .basic import BasicWorkflow, BasicLogger, Verbosity


class IslandWorkflow:
    """Workflow that runs multiple independent BasicWorkflows (islands) in sequence.
    
    Each island has its own isolated storage space to prevent interference between islands.
    The best result from all islands is selected as the final output.
    """
    
    def __init__(
        self,
        template_path: str,
        num_islands: int = 1,
        llm_model: str = "deepseek-chat",
        temperature: float = 0.7,
        tag: Optional[str] = None,
        score_input: Any = None,
        storage: Optional[ItemStorage] = None,
        verbosity: int = Verbosity.BASIC
    ):
        """Initialize island workflow with template and execution settings.
        
        Args:
            template_path: Path to template file
            num_islands: Number of independent islands to run
            llm_model: Name of LLM model to use
            temperature: Temperature parameter for LLM
            tag: Tag for scoring function (None uses first found)
            score_input: Input to pass to scoring function
            storage: Optional shared storage (will be split for islands)
            verbosity: Verbosity level (0-3)
        """
        if num_islands < 1:
            raise ValueError("num_islands must be at least 1")
            
        # Setup shared storage with splits - preserve existing storage if provided
        if storage is None:
            db = SQLiteStringDatabase(":memory:")
            self.shared_storage = ItemStorage(db)
        else:
            self.shared_storage = storage
        self.num_islands = num_islands
        self.logger = BasicLogger(verbosity)
        
        # Split storage for islands
        self.island_storages = split_item_storage(
            self.shared_storage, 
            num_islands, 
            "_island_id"
        )
        
        # Initialize islands
        self.islands = []
        for i, island_storage in enumerate(self.island_storages):
            self.islands.append(
                BasicWorkflow(
                    template_path=template_path,
                    llm_model=llm_model,
                    temperature=temperature,
                    tag=tag,
                    score_input=score_input,
                    storage=island_storage,
                    verbosity=verbosity,
                    logger=self.logger  # Share the same logger instance
                )
            )

    def generate(self, batch_size: int = 1, iterations: int = 1) -> Tuple[str, bool, float]:
        """Generate, validate and score function versions across all islands.
        
        Args:
            batch_size: Number of candidates to generate per iteration per island
            iterations: Number of iterations to run per island
            
        Returns:
            Tuple of (best_function_body, is_valid, highest_score) from all islands
        """
        best_body = ""
        best_score = float("-inf")
        best_valid = False
        
        for island_num, island in enumerate(self.islands):
            if self.logger.verbosity >= Verbosity.BASIC:
                self.logger.info(f"\n🏝️ Running Island {island_num+1}/{len(self.islands)}")
            
            body, valid, score = island.generate(batch_size, iterations)
            
            if score > best_score:
                best_body = body
                best_score = score
                best_valid = valid
            
            if self.logger.verbosity >= Verbosity.BASIC:
                self.logger.info(f"Island {island_num+1} Best Score: {score:.2f}")
        
        if len(self.islands) > 1 and self.logger.verbosity >= Verbosity.BASIC:
            self.logger.info(f"\n🏆 Best Overall Score: {best_score:.2f}")
            
        return best_body, best_valid, best_score
