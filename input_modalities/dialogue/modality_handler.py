"""
Dialogue modality handler.

Responsible for managing additional user information
required during neuro-symbolic reasoning.

Instead of using terminal input(), this module creates
requests that are displayed by the Streamlit UI.
"""

from __future__ import annotations

from typing import Any

from services.interaction_service import interaction



class DialogueModalityHandler:
    """
    Controls modality-based interaction.

    Example:

    Prolog requires:
        glucose value

    Handler creates:

        PendingQuestion(
            question="Random plasma glucose (mg/dL)",
            modality="numeric"
        )

    Streamlit displays the input widget.
    """



    def request_input(
        self,
        question: str,
        modality: str,
        options: list | None = None,
    ) -> None:
        """
        Send a request to the Streamlit interface.
        """

        interaction.request(
            question=question,
            modality=modality,
            options=options,
        )



    def needs_input(
        self
    ) -> bool:
        """
        Check if UI is waiting for an answer.
        """

        return interaction.has_question()



    def get_pending_question(
        self
    ):
        """
        Return current UI question.
        """

        return interaction.get_question()



    def get_answer(
        self
    ) -> Any:
        """
        Retrieve answer supplied by user.
        """

        return interaction.get_answer()



    def clear(
        self
    ) -> None:
        """
        Remove completed interaction.
        """

        interaction.clear()



    # ----------------------------------------------------
    # Convenience functions
    # ----------------------------------------------------


    def ask_numeric(
        self,
        question: str
    ) -> None:

        self.request_input(
            question,
            "numeric"
        )



    def ask_boolean(
        self,
        question: str
    ) -> None:

        self.request_input(
            question,
            "boolean"
        )



    def ask_string(
        self,
        question: str
    ) -> None:

        self.request_input(
            question,
            "string"
        )



    def ask_category(
        self,
        question: str,
        categories: list[str]
    ) -> None:

        self.request_input(
            question,
            "categorical",
            categories
        )



    def ask_range(
        self,
        question: str,
        start: int,
        stop: int
    ) -> None:

        self.request_input(
            question,
            "range",
            {
                "start": start,
                "stop": stop,
            }
        )



    def ask_duration(
        self,
        question: str
    ) -> None:

        self.request_input(
            question,
            "duration"
        )



    # ----------------------------------------------------
    # Response formatting
    # ----------------------------------------------------


    def adjust_response_behavior(
        self,
        modality: str | None,
        response: dict
    ) -> dict:
        """
        Adjust answer style depending on modality.
        """

        if modality == "boolean":

            response["style"] = "short"


        elif modality == "multiple_choice":

            response["style"] = "interactive"


        elif modality == "numeric":

            response["style"] = "explanatory"


        elif modality == "categorical":

            response["style"] = "label_focused"


        else:

            response["style"] = "default"



        return response