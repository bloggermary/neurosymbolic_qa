import time
import janus_swi as janus

from input_modalities.llm.query_generator import generate_query
from input_modalities.llm.response_translator import translate_result
from input_modalities.evaluation.metrics import load_json, save_json


KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"


def run_reasoning(query):
    query = query.rstrip(".").strip()
    return janus.query_once(query)


def run():
    data = load_json("evaluation/test_questions.json")

    results = []
    success = 0

    for item in data:
        q = item["question"]

        try:
            t0 = time.perf_counter()

            query = generate_query(q, "")

            result = run_reasoning(query)

            answer = translate_result(q, query, result)

            t1 = time.perf_counter()

            results.append({
                "question": q,
                "query": query,
                "result": str(result),
                "answer": answer,
                "time": t1 - t0,
                "success": True
            })

            success += 1

        except Exception as e:
            results.append({
                "question": q,
                "error": str(e),
                "success": False
            })

    save_json("evaluation/results/pipeline_results.json", results)
    save_json("evaluation/results/pipeline_success.json", {
        "success_rate": success / len(data)
    })

    print("Pipeline success rate:", success / len(data))


if __name__ == "__main__":
    run()