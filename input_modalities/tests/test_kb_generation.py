import pytest
from llm.kb_generator import KBGenerator


class FakeLLM:
    def __call__(self, prompt: str) -> str:
        return """
        disease(diabetes).
        symptom(diabetes, fatigue).
        symptom(diabetes, thirst).
        treatment(diabetes, insulin).
        """


@pytest.fixture
def kb_gen():
    return KBGenerator(FakeLLM())


def test_kb_contains_core_predicates(kb_gen):
    text = "Diabetes causes fatigue and thirst and is treated with insulin."

    kb = kb_gen.generate("diabetes", text)

    assert isinstance(kb, str)
    assert "disease(diabetes)" in kb
    assert "symptom(diabetes, fatigue)" in kb
    assert "treatment(diabetes, insulin)" in kb


def test_kb_is_not_empty(kb_gen):
    kb = kb_gen.generate("diabetes", "short text")

    assert kb.strip() != ""
    assert len(kb) > 20


def test_kb_stability_determinism(kb_gen):
    t = "Diabetes causes fatigue."

    kb1 = kb_gen.generate("diabetes", t)
    kb2 = kb_gen.generate("diabetes", t)

    assert kb1 == kb2