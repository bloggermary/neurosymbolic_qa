from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler
from modalities.multiple_category_handler import MultipleCategoryHandler
from modalities.multi_attribute_entity_handler import MultiAttributeEntityHandler

class ModalityRouter:
    """
    Routes modality-specific questions to the correct handler.
    """

    def __init__(self):
        self.boolean_handler = BooleanHandler()
        self.numeric_handler = NumericHandler()
        self.string_handler = StringHandler()
        self.multiple_category_handler = MultipleCategoryHandler()
        self.multi_attribute_entity_handler = MultiAttributeEntityHandler()


    def route_boolean(self, question: str) -> bool:
        return self.boolean_handler.handle(question)

    def route_numeric(self, question: str) -> float:
        return self.numeric_handler.handle(question)

    def route_string(self, question: str) -> str:
        return self.string_handler.handle(question)

    def route_category_multiple(self, question: str, categories: list[str]) -> list [str]:
        return self.multiple_category_handler.handle(question, categories)
    
    def route_multiple_attribute_entity(self, question: str, entity: str, fields: list[tuple[str, str, str]]) -> dict:
        return self.multi_attribute_entity_handler.handle(question, entity, fields)

router = ModalityRouter()


def route_boolean(question: str) -> bool:
    return router.route_boolean(question)


def route_numeric(question: str) -> float:
    return router.route_numeric(question)


def route_string(question: str) -> str:
    return router.route_string(question)


def route_category_multiple(question: str, categories: list[str]) -> list[str]:
    return router.route_category_multiple(question, categories) 

def route_multi_attribute_entity(question: str, entity: str, fields: list[tuple[str, str, str]]) -> dict:
    return router.route_multi_attribute_entity(question, entity, fields)

