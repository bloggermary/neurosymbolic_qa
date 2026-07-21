import time
from llm.query_generator import generate_query
from evaluation.testing_suite.metrics import (
    load_json,
    save_json,
    compute_accuracy,
    keyword_query_score,
)


# A query counts as "keyword correct" if, on average, this fraction of
# each expected predicate's meaningful words shows up in the generated
# query - forgiving of naming/ordering differences without accepting
# a query that's missing most of the intended meaning.
KEYWORD_MATCH_THRESHOLD = 0.7


def run():
    data = load_json("evaluation/tests/json_entries/test_questions.json")

    # Query generation needs to see real predicate names to ground its
    # answer in - passing "" here (as this test used to) forces the
    # model to guess blindly, which is not how it's used in production
    # (pipeline.ask() always passes the real generated KB text).
    with open(
        "evaluation/tests/json_entries/reference_kb.pl",
        encoding="utf-8",
    ) as kb_file:
        reference_kb = kb_file.read()

    results = []
    correct = 0
    keyword_correct = 0

    for item in data:
        question = item["question"]

        expected_contains = item.get("expected_query_contains", [])
        expected_predicates = item.get("expected_predicates", [])
        must_not = item.get("must_not_contain", [])

        start = time.perf_counter()
        query = generate_query(question, reference_kb)
        duration = time.perf_counter() - start

        # -----------------------------
        # Strict evaluation: every expected predicate must appear
        # verbatim as a substring of the query.
        # -----------------------------
        ok_contains = all(c.lower() in query.lower() for c in expected_contains)

        ok_predicates = all(p in query for p in expected_predicates)

        ok_forbidden = all(f.lower() not in query.lower() for f in must_not)

        ok = ok_contains and ok_predicates and ok_forbidden

        if ok:
            correct += 1

        # -----------------------------
        # Lenient evaluation: token/keyword overlap per predicate,
        # forgiving of naming/ordering differences (e.g. a model using
        # "fasting_glucose_value" instead of "fasting_glucose_mgdl"
        # still gets credit for capturing the right concept).
        # -----------------------------
        overlap = keyword_query_score(expected_predicates, query)

        ok_keyword = overlap >= KEYWORD_MATCH_THRESHOLD and ok_forbidden

        if ok_keyword:
            keyword_correct += 1

        results.append({
            "id": item["id"],
            "question": question,
            "query": query,
            "expected_predicates": expected_predicates,
            "expected_contains": expected_contains,
            "must_not_contain": must_not,
            "predicate_match": ok_predicates,
            "keyword_match": ok_contains,
            "keyword_overlap_score": overlap,
            "keyword_correct": ok_keyword,
            "correct": ok,
            "time": duration
        })

    acc = compute_accuracy(correct, len(data))
    keyword_acc = compute_accuracy(keyword_correct, len(data))

    save_json("evaluation/results/query_results.json", results)
    save_json("evaluation/results/query_accuracy.json", {
        "strict_accuracy": acc,
        "keyword_accuracy": keyword_acc,
    })

    print("Query Accuracy (strict):", acc)
    print("Query Accuracy (keyword overlap >= {:.0%}):".format(KEYWORD_MATCH_THRESHOLD), keyword_acc)


if __name__ == "__main__":
    run()