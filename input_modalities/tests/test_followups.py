import pytest
from llm.followup_generator import FollowupGenerator


class FakeLLM:
    def __call__(self, prompt: str) -> str:
        return """
        What are the symptoms of diabetes?
        How is diabetes diagnosed?
        What are the risk factors?
        """


@pytest.fixture
def followup_gen():
    return FollowupGenerator(FakeLLM())


def test_followup_count(followup_gen):
    result = followup_gen.generate(
        "What is diabetes?",
        "Diabetes is a metabolic disease.",
        n=3
    )

    assert isinstance(result, list)
    assert len(result) == 3


def test_followups_are_strings(followup_gen):
    result = followup_gen.generate(
        "What is diabetes?",
        "Diabetes is a disease.",
        n=3
    )

    assert all(isinstance(q, str) for q in result)


def test_followups_not_empty(followup_gen):
    result = followup_gen.generate(
        "What is diabetes?",
        "Answer",
        n=3
    )

    assert all(q.strip() != "" for q in result)


def test_followups_are_question_like(followup_gen):
    result = followup_gen.generate(
        "What is diabetes?",
        "Answer",
        n=3
    )

    # ensures question quality, not just random text
    for q in result:
        assert "?" in q


def test_followup_determinism(followup_gen):
    q = "What is diabetes?"
    a = "Diabetes is a disease."

    r1 = followup_gen.generate(q, a, n=3)
    r2 = followup_gen.generate(q, a, n=3)

    assert r1 == r2