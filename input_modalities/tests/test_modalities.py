from llm.modality_detector import ModalityDetector


class DummyLLM:
    def __call__(self, prompt):
        return "boolean"


def test_modality():
    det = ModalityDetector(DummyLLM())

    assert det.detect("Is diabetes dangerous?") == "boolean"