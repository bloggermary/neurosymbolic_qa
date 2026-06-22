from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler
from modalities.range_handler import RangeHandler
from modalities.duration_handler import DurationHandler

class ModalityRouter:
    """
    Routes modality-specific questions to the correct handler.
    """

    def __init__(self):
        self.boolean_handler = BooleanHandler()
        self.numeric_handler = NumericHandler()
        self.string_handler = StringHandler()
        self.range_handler = RangeHandler()
        self.duration_handler = DurationHandler()

    def route_boolean(self, question: str) -> bool:
        return self.boolean_handler.handle(question)

    def route_numeric(self, question: str) -> float:
        return self.numeric_handler.handle(question)

    def route_string(self, question: str) -> str:
        return self.string_handler.handle(question)

    def route_range(self, question: str, start: int, stop: int) -> int:
        return self.range_handler.handle(question, start, stop)    
    
    def route_duration(self, question: str) -> int:
        return self.duration_handler.handle(question)

router = ModalityRouter()


def route_boolean(question: str) -> bool:
    return router.route_boolean(question)


def route_numeric(question: str) -> float:
    return router.route_numeric(question)

def route_string(question: str) -> str:
    return router.route_string(question)

def route_range(question: str, start: int, stop: int) -> int:
    return router.route_range(question, start, stop)

def route_duration(question: str) -> int:
    return router.route_duration(question)