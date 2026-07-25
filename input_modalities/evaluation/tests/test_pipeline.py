"""
Full pipeline evaluation.

Unlike the component-level evals, this drives the REAL interactive
pipeline (services/pipeline.py's ask()/resume(), the same code path
the live Streamlit app uses) all the way to a completed answer, by
synthesizing an answer for whatever modality each pending question
turns out to be and resuming until the dialogue actually finishes.

Two things a first version of this eval got wrong, both fixed here:

1. It only ran against ONE knowledge base (the default snippet), so a
   "100% completion" result said nothing about the other five medical
   texts this project supports. This version also runs a smaller,
   domain-generic question set against every other snippet.

2. It always answered every question the exact same way (boolean
   always "yes", category always the first option, numeric always
   100.0), which means every run took the SAME branch through a given
   knowledge base's logic every time - a conditional branch like
   medication_details (multi_attribute_entity) could go completely
   untested for 100 runs in a row if "medication status" defaulted to
   "none" every single time. This version randomizes every synthetic
   answer and explicitly tracks which modalities were actually
   exercised across the whole run, so "it completed" and "it tested
   the full modality range" are reported as two separate, honest
   claims rather than conflated into one optimistic percentage.
"""

import random

from services.pipeline import pipeline
from services.interaction_service import interaction
from evaluation.testing_suite.metrics import load_json, save_json, compute_accuracy


MAX_TURNS = 40

ALL_MODALITIES = [
    "boolean", "numeric", "string", "category", "range", "duration",
    "multiple_category", "multi_structured_input", "multi_attribute_entity",
]

# A small, deliberately domain-generic set, safe to ask against ANY of
# the medical texts (not tied to one snippet's specific predicates),
# used to get real coverage of the other five knowledge bases without
# the cost of running the full 100-question set against every one.
GENERIC_QUESTIONS = [
    "Does this patient have diabetes?",
    "Please run a full diagnostic workup including symptoms, severity, duration, and current medications.",
    "Is the patient at low risk or high risk?",
    "What medications is the patient currently taking?",
    "Does the patient report any symptoms?",
]


def _synthetic_answer(pending, seen_modalities: set):
    """
    Builds a genuinely randomized answer for whatever modality the
    current pending question is, so repeated runs exercise different
    branches of the same knowledge base instead of always the same
    one. Records which modality was actually exercised.
    """

    modality = pending.modality
    options = pending.options
    seen_modalities.add(modality)

    if modality == "boolean":
        return random.choice(["yes", "no"])

    if modality == "numeric":
        return round(random.uniform(1, 300), 1)

    if modality == "duration":
        return round(random.uniform(0, 30), 1)

    if modality == "string":
        return random.choice([
            "No additional information.",
            "Patient reports mild symptoms.",
            "Nothing further to add.",
        ])

    if modality == "category":
        return random.choice(options) if options else "none"

    if modality == "range":
        lo = options.get("min", 0)
        hi = options.get("max", 10)
        return round(random.uniform(lo, hi), 1)

    if modality == "multiple_category":
        if not options:
            return []
        k = random.randint(0, len(options))
        return random.sample(options, k)

    if modality == "multi_structured_input":
        mode = options.get("mode", "sequence")
        groups = options.get("groups") or []
        if mode == "grouping":
            return {g: [f"item_{g}"] for g in groups}
        items = ["symptom_one", "symptom_two", "symptom_three"]
        random.shuffle(items)
        return items[:random.randint(1, 3)]

    if modality == "multi_attribute_entity":
        fields = options.get("fields", [])
        data = {}
        for field in fields:
            key, _prompt, field_type = field[0], field[1], field[2]
            if field_type == "int":
                data[key] = random.randint(1, 10)
            elif field_type == "float":
                data[key] = round(random.uniform(1, 500), 1)
            elif field_type == "bool":
                data[key] = random.choice([True, False])
            else:
                data[key] = "Sample value"
        return {"entity": options.get("entity", "entity"), "data": data}

    return "N/A"


def _run_one(question: str, snippet_name: str, seen_modalities: set) -> dict:

    pipeline.reset_dialogue()
    interaction.reset_all()

    try:
        response = pipeline.ask(question, snippet_name=snippet_name)
    except Exception as e:
        return {"outcome": "error", "error": str(e), "turns": 0}

    turn_count = 0

    while response.answer == "" and interaction.has_question():

        turn_count += 1

        if turn_count > MAX_TURNS:
            return {
                "outcome": "exceeded_max_turns",
                "error": None,
                "turns": turn_count,
            }

        pending = interaction.get_question()
        answer = _synthetic_answer(pending, seen_modalities)

        try:
            response = pipeline.resume(answer)
        except Exception as e:
            return {
                "outcome": "error",
                "error": str(e),
                "turns": turn_count,
            }

    return {
        "outcome": "completed",
        "error": None,
        "turns": turn_count,
        "answer_preview": response.answer[:200],
    }


def run():

    random.seed(0)

    data = load_json("evaluation/tests/json_entries/test_questions.json")

    cases = [
        {"id": item["id"], "question": item["question"], "snippet": pipeline.DEFAULT_SNIPPET}
        for item in data
    ]

    other_snippets = [
        s for s in pipeline.available_snippets()
        if s != pipeline.DEFAULT_SNIPPET
    ]

    for snippet in other_snippets:
        for i, question in enumerate(GENERIC_QUESTIONS):
            cases.append({
                "id": f"{snippet}_{i:02d}",
                "question": question,
                "snippet": snippet,
            })

    results = []
    completed = 0
    seen_modalities: set = set()

    for case in cases:

        outcome = _run_one(case["question"], case["snippet"], seen_modalities)

        success = outcome["outcome"] == "completed"

        if success:
            completed += 1

        results.append({
            "id": case["id"],
            "question": case["question"],
            "snippet": case["snippet"],
            "outcome": outcome["outcome"],
            "turns": outcome["turns"],
            "error": outcome["error"],
            "success": success,
        })

        print(
            f"{case['id']} [{case['snippet']}]: {outcome['outcome']} "
            f"({outcome['turns']} turns)"
            + (f" - {outcome['error'][:120]}" if outcome["error"] else "")
        )

    total = len(cases)
    success_rate = compute_accuracy(completed, total)

    unexercised_modalities = sorted(set(ALL_MODALITIES) - seen_modalities)
    modality_coverage = compute_accuracy(len(seen_modalities), len(ALL_MODALITIES))

    # A completion rate alone can't distinguish "the pipeline is robust"
    # from "the pipeline is robust for the one narrow path our synthetic
    # answers happen to take." overall_success folds coverage in
    # explicitly, so an unexercised modality actually shows up as a
    # number less than 100%, rather than a warning that's easy to miss
    # underneath a clean-looking completion rate.
    overall_success = min(success_rate, modality_coverage)

    save_json("evaluation/results/pipeline_results.json", results)
    save_json("evaluation/results/pipeline_success.json", {
        "total_questions": total,
        "completed": completed,
        "exceeded_max_turns": sum(1 for r in results if r["outcome"] == "exceeded_max_turns"),
        "failed": sum(1 for r in results if r["outcome"] == "error"),
        "success_rate": success_rate,
        "modality_coverage": modality_coverage,
        "overall_success": overall_success,
        "snippets_tested": sorted({c["snippet"] for c in cases}),
        "modalities_exercised": sorted(seen_modalities),
        "modalities_never_exercised": unexercised_modalities,
    })

    print(f"\nFull pipeline completion rate: {completed}/{total} ({success_rate:.0%})")
    print(f"Modality coverage: {len(seen_modalities)}/{len(ALL_MODALITIES)} ({modality_coverage:.0%})")
    print(f"Overall success (completion x coverage): {overall_success:.0%}")
    print(f"Snippets tested: {sorted({c['snippet'] for c in cases})}")
    print(f"Modalities actually exercised: {sorted(seen_modalities)}")

    if unexercised_modalities:
        print(f"WARNING - never exercised even once: {unexercised_modalities}")

    for r in results:
        if r["outcome"] != "completed":
            print(f"  {r['outcome'].upper()} {r['id']}: {r['question']!r} - {r['error']}")


if __name__ == "__main__":
    run()
