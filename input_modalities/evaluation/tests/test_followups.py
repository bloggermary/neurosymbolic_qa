from llm.followup_generator import generate_followup
from evaluation.testing_suite.metrics import load_json, save_json, compute_accuracy


def run():
    data = load_json("evaluation/tests/json_entries/test_modalities.json")

    results = []
    strict_correct = 0
    decision_correct = 0

    for item in data:
        question = item["question"]
        modality = item.get("expected_modality")
        expected = item.get("expected_followups", [])
        expected_needed = item.get("followup_expected", bool(expected))

        predicted = generate_followup(question, modality)

        expected_questions = [f["question"] for f in expected]
        predicted_questions = [f["question"] for f in predicted]

        # Strict: exact placeholder-text match. Kept for transparency,
        # but not a realistic bar - matching a hand-authored slug like
        # "thirst_duration" character-for-character isn't what actually
        # matters here.
        strict_ok = set(expected_questions) == set(predicted_questions)
        strict_correct += int(strict_ok)

        # Decision correctness: did we correctly decide whether a
        # follow-up is needed at all, and if so, does its modality make
        # sense (not necessarily wording an identical question)?
        predicted_needed = len(predicted) > 0

        if expected_needed == predicted_needed:

            if not expected_needed:
                decision_ok = True
            else:
                expected_modalities = {f["modality"] for f in expected}
                predicted_modalities = {f["modality"] for f in predicted}
                decision_ok = bool(expected_modalities & predicted_modalities)

        else:
            decision_ok = False

        decision_correct += int(decision_ok)

        results.append({
            "question": question,
            "modality": modality,
            "expected_followup_needed": expected_needed,
            "predicted_followup_needed": predicted_needed,
            "expected": expected_questions,
            "predicted": predicted_questions,
            "strict_correct": strict_ok,
            "decision_correct": decision_ok,
            "followups": predicted
        })

    save_json("evaluation/results/followup_results.json", results)

    save_json("evaluation/results/followup_accuracy.json", {
        "strict_accuracy": compute_accuracy(strict_correct, len(data)),
        "decision_accuracy": compute_accuracy(decision_correct, len(data)),
    })

    print("Follow-up strict accuracy:", compute_accuracy(strict_correct, len(data)))
    print("Follow-up decision accuracy:", compute_accuracy(decision_correct, len(data)))


if __name__ == "__main__":
    run()
