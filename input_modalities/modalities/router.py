from llm.modality_detector import detect_modality

from modalities.boolean_handler import handle_boolean
from modalities.numeric_handler import handle_numeric
from modalities.string_handler import handle_string

def route_boolean(question: str) -> bool:
    return handle_boolean(question)


def route_numeric(question: str) -> float:
    return handle_numeric(question)


def route_string(question: str) -> str:
    return handle_string(question)