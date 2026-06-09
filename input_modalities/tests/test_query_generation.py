import pytest
from llm.query_generator import QueryGenerator


class FakeLLM:
    def __call__(self, prompt: str) -> str:
        return "possible_diagnosis([fatigue, thirst], diabetes)."


@pytest.fixture
def query_gen():
    return QueryGenerator(FakeLLM())


def test_query_generation_boolean(query_gen):
    q = query_gen.generate(
        "Does diabetes cause fatigue?",
        modality="boolean"
    )

    assert isinstance(q, str)
    assert "possible_diagnosis" in q or "disease" in q


def test_query_generation_numeric(query_gen):
    q = query_gen.generate(
        "How many symptoms does diabetes have?",
        modality="numeric"
    )

    assert isinstance(q, str)


def test_query_generation_valid_syntax_structure(query_gen):
    q = query_gen.generate(
        "What disease causes thirst?",
        modality="categorical"
    )

    # Basic Prolog sanity checks
    assert "(" in q
    assert ")" in q
    assert isinstance(q, str)


def test_query_not_empty(query_gen):
    q = query_gen.generate("What is diabetes?", "string")

    assert q.strip() != ""