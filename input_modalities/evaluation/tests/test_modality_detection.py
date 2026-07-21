import time
from llm.modality_detector import detect_modality  # adjust if needed
from evaluation.testing_suite.metrics import load_json, save_json, compute_accuracy


def run():
    data = load_json("evaluation/tests/json_entries/test_modalities.json")

    results = []
    correct = 0

    for item in data:
        q = item["question"]
        expected = item["expected_modality"]

        start = time.perf_counter()
        pred = detect_modality(q)
        duration = time.perf_counter() - start

        ok = pred == expected
        correct += int(ok)

        results.append({
            "question": q,
            "expected": expected,
            "predicted": pred,
            "correct": ok,
            "time": duration,

        })

    acc = compute_accuracy(correct, len(data))

    save_json("evaluation/results/modality_results.json", results)
    save_json("evaluation/results/modality_accuracy.json", {"accuracy": acc})

    print("Modality Accuracy:", acc)


if __name__ == "__main__":
    run()