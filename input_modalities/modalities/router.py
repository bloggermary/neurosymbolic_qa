from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler


class ModalityRouter:
    """
    Routes modality-specific questions to the correct handler.
    """

    def __init__(self):
        self.boolean_handler = BooleanHandler()
        self.numeric_handler = NumericHandler()
        self.string_handler = StringHandler()

    def route_boolean(self, question: str) -> bool:
        return self.boolean_handler.handle(question)

    def route_numeric(self, question: str) -> float:
        return self.numeric_handler.handle(question)

    def route_string(self, question: str) -> str:
        return self.string_handler.handle(question)


router = ModalityRouter()


def route_boolean(question: str) -> bool:
    return router.route_boolean(question)


def route_numeric(question: str) -> float:
    return router.route_numeric(question)


def route_string(question: str) -> str:
    return router.route_string(question)