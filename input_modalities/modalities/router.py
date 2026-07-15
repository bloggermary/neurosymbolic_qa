"""
Modality router.

This module routes modality requests to the correct handler.
The actual interaction is handled by the Streamlit UI through
the InteractionService.
"""

from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler
from modalities.category_handler import CategoryHandler
from modalities.range_handler import RangeHandler
from modalities.duration_handler import DurationHandler
from modalities.scale_handler import ScaleHandler


class ModalityRouter:
    """
    Routes modality-specific questions to the correct handler.
    """

    def __init__(self):

        self.boolean_handler = BooleanHandler()
        self.numeric_handler = NumericHandler()
        self.string_handler = StringHandler()
        self.category_handler = CategoryHandler()
        self.range_handler = RangeHandler()
        self.duration_handler = DurationHandler()
        self.scale_handler = ScaleHandler()


    def route_boolean(
        self,
        question: str
    ) -> bool | None:

        return self.boolean_handler.handle(
            question
        )


    def route_numeric(
        self,
        question: str
    ) -> float | None:

        return self.numeric_handler.handle(
            question
        )


    def route_string(
        self,
        question: str
    ) -> str | None:

        return self.string_handler.handle(
            question
        )


    def route_category(
        self,
        question: str,
        categories: list[str]
    ) -> str | None:

        return self.category_handler.handle(
            question,
            categories
        )


    def route_range(
        self,
        question: str,
        start: int,
        stop: int
    ) -> dict:

        return self.range_handler.handle(
            question,
            start,
            stop
        )


    def route_duration(
        self,
        question: str
    ) -> dict:

        return self.duration_handler.handle(
            question
        )


    def route_scale(
        self,
        question: str,
        min_value: int,
        max_value: int
    ) -> dict:

        return self.scale_handler.handle(
            question,
            min_value,
            max_value
        )


# Global router instance

router = ModalityRouter()



# ---------------------------------------------------------
# Public functions used by the pipeline
# ---------------------------------------------------------


def route_boolean(
    question: str
) -> bool | None:

    return router.route_boolean(question)



def route_numeric(
    question: str
) -> float | None:

    return router.route_numeric(question)



def route_string(
    question: str
) -> str | None:

    return router.route_string(question)



def route_category(
    question: str,
    categories: list[str]
) -> str | None:

    return router.route_category(
        question,
        categories
    )



def route_range(
    question: str,
    start: int,
    stop: int
) -> dict:

    return router.route_range(
        question,
        start,
        stop
    )



def route_duration(
    question: str
) -> dict:

    return router.route_duration(
        question
    )



def route_scale(
    question: str,
    min_value: int = 1,
    max_value: int = 10
) -> dict:

    return router.route_scale(
        question,
        min_value,
        max_value
    )