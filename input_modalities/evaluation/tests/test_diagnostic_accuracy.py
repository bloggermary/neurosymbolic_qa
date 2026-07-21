"""
Diagnostic accuracy evaluation.

The other evals check individual components (does modality detection
pick the right widget, does query generation name the right predicate,
does the pipeline avoid crashing). None of them check the thing that
actually matters for a diagnostic system: given a real patient's
answers, does the reasoning reach the CORRECT verdict?

This drives the reference KB (evaluation/tests/json_entries/reference_kb.pl)
through realistic patient scenarios with known, medically-grounded
ground-truth verdicts - including boundary conditions on every
threshold, since that's where off-by-one logic bugs actually hide -
and checks diagnose/1's output against the expected verdict.
"""

import janus_swi as janus

from services.interaction_service import interaction
from evaluation.testing_suite.metrics import load_json, save_json, compute_accuracy


REFERENCE_KB_PATH = "evaluation/tests/json_entries/reference_kb.pl"
SCENARIOS_PATH = "evaluation/tests/json_entries/test_diagnostic_scenarios.json"


def run():

    janus.consult(REFERENCE_KB_PATH)

    scenarios = load_json(SCENARIOS_PATH)

    results = []
    correct = 0

    for scenario in scenarios:

        interaction.reset_all()

        for question, answer in scenario["answers"].items():
            interaction.remember(question, float(answer))

        error = None
        verdict = None

        try:
            outcome = janus.query_once("diagnose(Verdict)")
            verdict = outcome.get("Verdict") if outcome else None
        except Exception as e:
            error = str(e)

        is_correct = verdict == scenario["expected_verdict"]

        if is_correct:
            correct += 1

        results.append({
            "id": scenario["id"],
            "description": scenario.get("description", ""),
            "answers": scenario["answers"],
            "expected_verdict": scenario["expected_verdict"],
            "actual_verdict": verdict,
            "correct": is_correct,
            "error": error,
        })

    interaction.reset_all()

    total = len(scenarios)
    accuracy = compute_accuracy(correct, total)

    save_json("evaluation/results/diagnostic_results.json", results)
    save_json("evaluation/results/diagnostic_accuracy.json", {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
    })

    print(f"Diagnostic accuracy: {correct}/{total} ({accuracy:.0%})")

    for r in results:
        if not r["correct"]:
            print(
                f"  FAILED {r['id']} ({r['description']}): "
                f"expected={r['expected_verdict']} actual={r['actual_verdict']} "
                f"error={r['error']}"
            )


if __name__ == "__main__":
    run()
