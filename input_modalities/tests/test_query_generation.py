from llm.query_generator import QueryGenerator


def test_query_generation(llm_client):
    gen = QueryGenerator(llm_client)

    q = gen.generate("Does diabetes cause fatigue?", "boolean")

    assert isinstance(q, str)
    assert len(q) > 0