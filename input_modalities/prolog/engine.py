import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PrologEngine:
    """
    Manages Prolog knowledge base loading and runtime state.

    This does NOT execute queries directly.
    It only manages KB lifecycle.
    """

    kb_path: Optional[str] = None

    def load_kb(self, file_path: str) -> None:
        """
        Load a Prolog knowledge base.

        Args:
            file_path: Path to .pl file
        """
        try:
            self.kb_path = file_path
            logger.info(f"Prolog KB loaded: {file_path}")

        except Exception as e:
            logger.exception("Failed to load Prolog KB")
            raise RuntimeError(f"Could not load KB: {e}")

    def get_kb(self) -> str:
        """
        Returns current KB path.

        Raises:
            RuntimeError if KB not loaded
        """
        if not self.kb_path:
            raise RuntimeError("No Prolog KB loaded")

        return self.kb_path