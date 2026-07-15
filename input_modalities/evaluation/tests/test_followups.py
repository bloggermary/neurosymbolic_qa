from llm.followup_generator import generate_followup
from evaluation.metrics  import load_json, save_json, compute_accuracy


def run():
    data = load_json("evaluation/tests/json_entries/test_modalities.json")

    results = []
    correct = 0

    for item in data:
        question = item["question"]
        expected = item.get("expected_followups", [])

        predicted = generate_followup(question)

        expected_questions = [f["question"] for f in expected]
        predicted_questions = [f["question"] for f in predicted]

        ok = set(expected_questions) == set(predicted_questions)
        correct += int(ok)

        results.append({
            "question": question,
            "expected": expected_questions,
            "predicted": predicted_questions,
            "correct": ok,
            "followups": predicted
        })

    save_json("evaluation/results/followup_results.json", results)

    save_json("evaluation/results/followup_accuracy.json", {
        "accuracy": compute_accuracy(correct, len(data))
    })

    print("Follow-up accuracy:", compute_accuracy(correct, len(data)))


if __name__ == "__main__":
    run()