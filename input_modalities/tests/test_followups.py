from llm.followup_generator import FollowupGenerator


def test_followups(llm_client):
    gen = FollowupGenerator(llm_client)

    res = gen.generate(
        "What is diabetes?",
        "Diabetes is a metabolic disease.",
        n=3
    )

    assert len(res) == 3