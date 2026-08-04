from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler
from modalities.category_handler import CategoryHandler
from modalities.range_handler import RangeHandler
from modalities.duration_handler import DurationHandler
from modalities.multiple_category_handler import MultipleCategoryHandler
from modalities.multi_attribute_entity_handler import MultiAttributeEntityHandler
from modalities.multi_structured_input_handler import MultiStructuredInputHandler


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
        self.category_handler = CategoryHandler()
        self.multiple_category_handler = MultipleCategoryHandler()
        self.multi_attribute_entity_handler = MultiAttributeEntityHandler()
        self.multi_structured_input_handler = MultiStructuredInputHandler()

    def route_boolean(self, question: str) -> bool:
        return self.boolean_handler.handle(question)

    def route_numeric(self, question: str) -> float:
        return self.numeric_handler.handle(question)

    def route_string(self, question: str) -> str:
        return self.string_handler.handle(question)
    
    def route_category(self, question: str, categories: list[str]) -> str:
        return self.category_handler.handle(question, categories)

    def route_range(self, question: str, start: int, stop: int) -> int:
        return self.range_handler.handle(question, start, stop)    
    
    def route_duration(self, question: str) -> int:
        return self.duration_handler.handle(question)

    def route_category_multiple(self, question: str, categories: list[str]) -> list [str]:
        return self.multiple_category_handler.handle(question, categories)
    
    def route_multiple_attribute_entity(self, question: str, entity: str, fields: list[tuple[str, str, str]]) -> dict:
        return self.multi_attribute_entity_handler.handle(question, entity, fields)
    
    def route_multi_structured_input(self, question: str, mode: str, groups: list[str] | None = None):
        return self.multi_structured_input_handler(question, mode, groups)
    
    

router = ModalityRouter()


def route_boolean(question: str) -> bool:
    return router.route_boolean(question)

def route_numeric(question: str) -> float:
    return router.route_numeric(question)

def route_string(question: str) -> str:
    return router.route_string(question)

def route_category(question: str, categories: list[str]) -> str:
    return router.route_category(question, categories)

def route_range(question: str, start: int, stop: int) -> int:
    return router.route_range(question, start, stop)

def route_duration(question: str) -> int:
    return router.route_duration(question)

def route_category_multiple(question: str, categories: list[str]) -> list[str]:
    return router.route_category_multiple(question, categories) 

def route_multi_attribute_entity(question: str, entity: str, fields: list[tuple[str, str, str]]) -> dict:
    return router.route_multi_attribute_entity(question, entity, fields)

def route_multi_structured_input(question: str, mode: str, groups: list[str] | None = None):
    return router.route_multi_structured_input(question, mode, groups)

