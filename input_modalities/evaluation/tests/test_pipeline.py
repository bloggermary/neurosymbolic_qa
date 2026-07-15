import time
import os
import janus_swi as janus

from llm.query_generator import generate_query
from llm.response_translator import translate_result
from evaluation.metrics import load_json, save_json


KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"


def load_kb():
    """
    Load the Prolog knowledge base before executing queries.
    """
    if not os.path.exists(KB_PATH):
        raise FileNotFoundError(
            f"Knowledge base not found: {KB_PATH}"
        )

    janus.consult(KB_PATH)


def run_reasoning(query):
    """
    Execute generated Prolog query.
    """
    query = query.rstrip(".").strip()

    return janus.query_once(query)


def run():

    print("Loading Prolog KB...")
    load_kb()
    print("KB loaded successfully.")

    data = load_json(
        "evaluation/tests/json_entries/test_questions.json"
    )

    results = []

    success_count = 0

    for item in data:

        question = item["question"]

        try:

            start = time.perf_counter()

            # Generate Prolog query
            query = generate_query(
                question,
                ""
            )

            # Execute query
            result = run_reasoning(query)

            # Translate answer
            answer = translate_result(
                question,
                query,
                result
            )

            end = time.perf_counter()


            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "expected_predicates": item.get(
                        "expected_predicates",
                        []
                    ),
                    "query": query,
                    "result": str(result),
                    "answer": answer,
                    "time": end - start,
                    "success": True
                }
            )


            success_count += 1


        except Exception as e:

            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "error": str(e),
                    "success": False
                }
            )


    total = len(data)

    success_rate = (
        success_count / total
        if total > 0
        else 0
    )


    # Detailed results for analysis
    save_json(
        "evaluation/results/pipeline_results.json",
        results
    )


    # Better metric format for plotting
    save_json(
        "evaluation/results/pipeline_success.json",
        {
            "total_questions": total,
            "successful": success_count,
            "failed": total - success_count,
            "success_rate": success_rate
        }
    )


    print(
        f"Pipeline success rate: {success_rate:.2%}"
    )


if __name__ == "__main__":
    run()