import pytest
from llm.modality_detector import ModalityDetector


class FakeLLM:
    def __call__(self, prompt: str) -> str:
        if "how many" in prompt.lower():
            return "numeric"
        if "is" in prompt.lower():
            return "boolean"
        return "categorical"


@pytest.fixture
def detector():
    return ModalityDetector(FakeLLM())


def test_boolean_detection(detector):
    assert detector.detect("Is diabetes dangerous?") == "boolean"


def test_numeric_detection(detector):
    assert detector.detect("How many symptoms does diabetes have?") == "numeric"


def test_categorical_detection(detector):
    assert detector.detect("What disease causes thirst?") == "categorical"


def test_unknown_input_still_returns_valid(detector):
    out = detector.detect("????")

    assert out in ["boolean", "numeric", "categorical", "string", "multiple_choice"]