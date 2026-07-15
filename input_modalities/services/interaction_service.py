"""
Interaction service.

Acts as a bridge between:
- Prolog/Pipeline requesting information
- Streamlit UI collecting the answer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PendingQuestion:
    """
    Represents a question waiting for the user.
    """

    question: str
    modality: str
    options: list | dict | None = None
    answer: Any | None = None



class InteractionService:

    def __init__(self):

        self.pending_question: PendingQuestion | None = None



    def request(
        self,
        question: str,
        modality: str,
        options=None,
    ):
        """
        Called by Prolog bridge when input is required.
        """

        self.pending_question = PendingQuestion(
            question=question,
            modality=modality,
            options=options,
        )



    def has_question(self) -> bool:

        return self.pending_question is not None



    def get_question(self):

        return self.pending_question



    def set_answer(
        self,
        answer: Any
    ):
        """
        Called by Streamlit after user submits input.
        """

        if self.pending_question:

            self.pending_question.answer = answer



    def has_answer(self) -> bool:

        return (
            self.pending_question is not None
            and self.pending_question.answer is not None
        )



    def get_answer(self):

        if self.pending_question:

            return self.pending_question.answer

        return None



    def clear(self):

        self.pending_question = None



    def reset_answer(self):

        """
        Keep the question but remove old answer.
        """

        if self.pending_question:

            self.pending_question.answer = None



interaction = InteractionService()