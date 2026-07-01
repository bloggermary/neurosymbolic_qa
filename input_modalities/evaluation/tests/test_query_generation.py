import time
from input_modalities.llm.query_generator import generate_query
from input_modalities.evaluation.metrics import load_json, save_json, compute_accuracy


def run():
    data = load_json("tests/test_questions.json")

    results = []
    correct = 0

    for item in data:
        question = item["question"]

        expected_contains = item.get("expected_query_contains", [])
        expected_predicates = item.get("expected_predicates", [])
        must_not = item.get("must_not_contain", [])

        start = time.perf_counter()
        query = generate_query(question, "")
        duration = time.perf_counter() - start

        # -----------------------------
        # Evaluation logic (NEW CORE)
        # -----------------------------
        ok_contains = all(c.lower() in query.lower() for c in expected_contains)

        ok_predicates = all(p in query for p in expected_predicates)

        ok_forbidden = all(f.lower() not in query.lower() for f in must_not)

        ok = ok_contains and ok_predicates and ok_forbidden

        if ok:
            correct += 1

        results.append({
            "id": item["id"],
            "question": question,
            "query": query,
            "expected_predicates": expected_predicates,
            "expected_contains": expected_contains,
            "must_not_contain": must_not,
            "predicate_match": ok_predicates,
            "keyword_match": ok_contains,
            "correct": ok,
            "time": duration
        })

    acc = compute_accuracy(correct, len(data))

    save_json("tests/results/query_results.json", results)
    save_json("tests/results/query_accuracy.json", {"accuracy": acc})

    print("Query Accuracy:", acc)


if __name__ == "__main__":
    run()