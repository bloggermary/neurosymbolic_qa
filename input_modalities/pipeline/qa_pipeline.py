import logging
from typing import Dict, Any

from llm.query_generator import QueryGenerator
from llm.modality_detector import ModalityDetector
from llm.response_translator import ResponseTranslator
from prolog.executor import PrologExecutor
from dialogue.state_manager import StateManager


logger = logging.getLogger(__name__)


class QAPipeline:
    """
    Core QA orchestration pipeline.

    Responsibilities:
        - Detect question modality
        - Translate NL question → Prolog query
        - Execute query in Prolog engine
        - Translate result → natural language
        - Maintain dialogue state
    """

    def __init__(self, llm_client, kb_path: str):
        self.llm_client = llm_client

        self.modality_detector = ModalityDetector(llm_client)
        self.query_generator = QueryGenerator(llm_client)
        self.translator = ResponseTranslator(llm_client)

        self.executor = PrologExecutor(kb_path)
        self.state = StateManager()

        self.kb_path = kb_path

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Executes full QA pipeline.

        Args:
            question: Natural language medical question

        Returns:
            Structured response containing all intermediate steps
        """

        logger.info(f"Received question: {question}")

        try:
            modality = self.modality_detector.detect(question)
            logger.debug(f"Detected modality: {modality}")

            prolog_query = self.query_generator.generate(
                question=question,
                modality=modality
            )

            logger.debug(f"Generated Prolog query: {prolog_query}")

            raw_answer = self.executor.run(prolog_query)

            final_answer = self.translator.translate(
                question=question,
                prolog_answer=raw_answer,
                modality=modality
            )

            self.state.update(question, final_answer)

            return {
                "question": question,
                "modality": modality,
                "prolog_query": prolog_query,
                "raw_answer": raw_answer,
                "final_answer": final_answer
            }

        except Exception as e:
            logger.exception("QA pipeline failed")
            return {
                "question": question,
                "error": str(e),
                "final_answer": "An error occurred while processing your question."
            }