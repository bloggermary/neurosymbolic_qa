from input_modalities.evaluation.metrics import (
    load_json,
    save_json,
    compute_query_complexity,
    average_complexity,
    average_followups,
    compute_error_rate
)


def run():
    data = load_json("tests/results/pipeline_results.json")

    enriched = []

    for r in data:
        query = r.get("query", "")

        r["complexity"] = compute_query_complexity(query)

        enriched.append(r)

    avg_complexity = average_complexity(enriched)
    avg_followups = average_followups(enriched)
    error_rate = compute_error_rate(enriched)

    save_json("tests/results/complexity_metrics.json", {
        "avg_complexity": avg_complexity,
        "avg_followups": avg_followups,
        "error_rate": error_rate
    })

    print("Avg complexity:", avg_complexity)
    print("Avg followups:", avg_followups)
    print("Error rate:", error_rate)


if __name__ == "__main__":
    run()