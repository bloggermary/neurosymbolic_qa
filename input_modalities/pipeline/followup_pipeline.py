import logging
from typing import List

from llm.followup_generator import FollowupGenerator
from dialogue.followup_manager import FollowupManager


logger = logging.getLogger(__name__)


class FollowupPipeline:
    """
    Generates medically relevant follow-up questions based on QA context.

    This helps:
        - simulate dialogue
        - expand dataset
        - improve evaluation coverage
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.generator = FollowupGenerator(llm_client)
        self.manager = FollowupManager()

    def generate_followups(
        self,
        question: str,
        answer: str,
        n: int = 3
    ) -> List[str]:
        """
        Generate follow-up questions.

        Args:
            question: original user question
            answer: system answer
            n: number of follow-ups

        Returns:
            list of follow-up questions
        """

        logger.info("Generating follow-up questions")

        followups = self.generator.generate(
            question=question,
            answer=answer,
            n=n
        )

        if not isinstance(followups, list):
            raise ValueError("Followup generator must return a list")

        self.manager.store(question, followups)

        return followups