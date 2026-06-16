import os
import logging
from typing import Optional

from llm.kb_generator import KBGenerator
from prolog.engine import PrologEngine


logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Responsible for converting unstructured medical text into a structured
    Prolog knowledge base.

    Steps:
        1. Accept raw domain text
        2. Use LLM to extract logical structure
        3. Convert into Prolog facts/rules
        4. Persist KB to disk
        5. Load into Prolog engine for immediate querying
    """

    def __init__(
        self,
        llm_client,
        output_dir: str = "prolog/generated_kbs",
        engine: Optional[PrologEngine] = None
    ):
        self.llm_client = llm_client
        self.kb_generator = KBGenerator(llm_client)
        self.engine = engine or PrologEngine()

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def build_kb(self, topic: str, text: str) -> str:
        """
        Generates a Prolog KB from text and stores it on disk.

        Args:
            topic: Name of the medical topic (e.g., diabetes)
            text: Raw medical description

        Returns:
            Path to generated Prolog file
        """

        logger.info(f"Generating KB for topic={topic}")

        try:
            prolog_code = self.kb_generator.generate(topic=topic, text=text)

            if not prolog_code or len(prolog_code.strip()) < 10:
                raise ValueError("Generated KB is empty or invalid")

            file_path = os.path.join(self.output_dir, f"{topic}.pl")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(prolog_code)

            logger.info(f"KB written to {file_path}")

            self.engine.load_kb(file_path)

            return file_path

        except Exception as e:
            logger.exception("KB generation failed")
            raise RuntimeError(f"Ingestion pipeline failed: {e}")