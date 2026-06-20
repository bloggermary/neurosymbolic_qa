import pytest
from pipeline.qa_pipeline import QAPipeline


class FakeLLM:
    def __call__(self, prompt: str) -> str:
        return "boolean"


class FakeExecutor:
    def __init__(self):
        self.last_query = None

    def run(self, query: str):
        self.last_query = query
        return ["diabetes"]


@pytest.fixture
def pipeline():
    p = QAPipeline(FakeLLM(), kb_path="fake.pl")
    p.executor = FakeExecutor()
    return p


def test_pipeline_returns_complete_structure(pipeline):
    result = pipeline.ask("Does diabetes cause fatigue?")

    assert "question" in result
    assert "modality" in result
    assert "prolog_query" in result
    assert "raw_answer" in result
    assert "final_answer" in result


def test_pipeline_prolog_query_is_used(pipeline):
    result = pipeline.ask("Does diabetes cause fatigue?")

    assert pipeline.executor.last_query is not None
    assert isinstance(pipeline.executor.last_query, str)


def test_pipeline_handles_execution_gracefully(pipeline):
    result = pipeline.ask("Is diabetes dangerous?")

    assert result["final_answer"] is not None


def test_pipeline_deterministic_structure(pipeline):
    r1 = pipeline.ask("Is diabetes dangerous?")
    r2 = pipeline.ask("Is diabetes dangerous?")

    assert r1.keys() == r2.keys()