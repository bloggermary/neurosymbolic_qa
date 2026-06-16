import pytest
from pipeline.qa_pipeline import QAPipeline


class DummyLLM:
    def __call__(self, *args, **kwargs):
        return "mock"


class DummyExecutor:
    def run(self, query):
        return ["diabetes"]


@pytest.fixture
def pipeline(monkeypatch):
    pipe = QAPipeline(DummyLLM(), kb_path="fake.pl")
    pipe.executor = DummyExecutor()
    return pipe


def test_full_pipeline_execution(pipeline):
    result = pipeline.ask("Does diabetes cause fatigue?")

    assert "final_answer" in result
    assert "modality" in result
    assert "prolog_query" in result