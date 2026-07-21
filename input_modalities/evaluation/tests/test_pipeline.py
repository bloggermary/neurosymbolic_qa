import time
import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result
from evaluation.testing_suite.metrics import load_json, save_json


SNIPPET_PATH = "data/snippets/diabetes.txt"
KB_PATH = "prolog/generated_kb/diabetes.pl"


def load_kb() -> str:
    """
    Build a fresh knowledge base from the current generator and
    consult it. Returns the KB source text so the same text can be
    used to ground generate_query() - a stale, pre-existing .pl file
    would silently drift from whatever kb_generator.py currently
    produces, and testing against mismatched predicates would fail
    for reasons unrelated to reasoning quality.
    """

    with open(SNIPPET_PATH, encoding="utf-8") as file:
        medical_text = file.read()

    kb_code = generate_prolog_kb(medical_text)

    with open(KB_PATH, "w", encoding="utf-8") as file:
        file.write(kb_code)

    janus.consult(KB_PATH)

    return kb_code


def run_reasoning(query):
    """
    Execute generated Prolog query.
    """
    query = query.rstrip(".").strip()

    return janus.query_once(query)


def run():

    print("Loading Prolog KB...")
    kb_code = load_kb()
    print("KB loaded successfully.")

    data = load_json(
        "evaluation/tests/json_entries/test_questions.json"
    )

    results = []

    success_count = 0

    needs_input_count = 0

    for item in data:

        question = item["question"]

        try:

            start = time.perf_counter()

            # Generate Prolog query, grounded in the actual loaded KB
            query = generate_query(
                question,
                kb_code
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
                    "success": True,
                    "needs_input": False
                }
            )


            success_count += 1


        except Exception as e:

            message = str(e)

            # The KB always asks for missing clinical data interactively
            # (ask_numeric/ask_boolean/...) - correctly recognizing that
            # more input is needed is expected, correct behavior for this
            # domain, not a pipeline failure. Only genuine errors (syntax
            # errors, undefined predicates, bad queries) count as failures.
            is_needs_input = "WaitingForUserInput" in message

            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "error": message,
                    "success": is_needs_input,
                    "needs_input": is_needs_input
                }
            )

            if is_needs_input:
                success_count += 1
                needs_input_count += 1


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
            "answered_directly": success_count - needs_input_count,
            "needs_input": needs_input_count,
            "failed": total - success_count,
            "success_rate": success_rate
        }
    )


    print(
        f"Pipeline success rate: {success_rate:.2%}"
    )


if __name__ == "__main__":
    run()