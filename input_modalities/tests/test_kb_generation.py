import pytest
from llm.kb_generator import KBGenerator


class DummyLLM:
    def __call__(self, prompt):
        return "disease(diabetes). symptom(diabetes, fatigue)."


def test_kb_generator(tmp_path):
    gen = KBGenerator(DummyLLM())

    output = gen.generate("diabetes", "Diabetes causes fatigue")

    assert "disease" in output
    assert "symptom" in output