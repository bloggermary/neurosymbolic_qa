"""
Diagnostic accuracy evaluation.

The other evals check individual components (does modality detection
pick the right widget, does query generation name the right predicate,
does the pipeline avoid crashing). This one checks the thing that
actually matters for a diagnostic system: given a real patient's
answers, does the reasoning reach the CORRECT verdict.

It has two genuinely different parts, because they test two different
things and neither can substitute for the other:

1. run() drives the hand-written reference KB
   (evaluation/tests/json_entries/reference_kb.pl) through 200
   scenarios with known, medically-grounded ground-truth verdicts,
   including exact threshold boundaries. This tests whether the
   diagnostic REASONING PATTERN is internally consistent and free of
   logic bugs (off-by-one thresholds, wrong boolean precedence, etc.).
   Important limitation, stated plainly: both the Prolog logic and the
   Python verdict() function used to label the scenarios were written
   by the same author from the same understanding of the ADA
   criteria. A threshold transcribed identically wrong on both sides
   would score 100% here and never be caught - this test proves
   internal consistency, not independent correctness, and it never
   touches the actual LLM-driven KB generator at all.

2. run_fresh_generation_check() exists specifically to cover that gap:
   it generates a brand-new knowledge base from the real diabetes.txt
   source text (the same generator, gpt-5-mini, real product code
   path), and drives it through the REAL interactive pipeline with two
   clinically unambiguous scenarios (unmistakably diabetic values, and
   unmistakably normal values). Because a fresh generation's exact
   question wording and predicate names aren't known in advance, this
   can't compare a structured Verdict field the way run() does -
   instead it checks the final natural-language answer for the
   expected verdict keyword. That's a coarser check, but it is the
   only one of the two that touches the actual generator an LLM call
   produces, rather than a hand-written stand-in for it.
"""

import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from services.pipeline import pipeline
from services.interaction_service import interaction
from evaluation.testing_suite.metrics import load_json, save_json, compute_accuracy


REFERENCE_KB_PATH = "evaluation/tests/json_entries/reference_kb.pl"
SCENARIOS_PATH = "evaluation/tests/json_entries/test_diagnostic_scenarios.json"
FRESH_GEN_SNIPPET_TEXT_PATH = "data/snippets/diabetes.txt"


def _cache_answer(question: str, answer) -> None:
    """
    Caches an answer with its natural type. Numeric-looking answers
    (int/float, or a numeric string) are stored as floats to match
    what ask_numeric/ask_range/ask_duration expect; everything else
    (booleans, category strings, multi-select lists, multi-attribute
    dicts, free text) is stored as-is, since blindly float()-casting
    every answer breaks the moment a scenario includes anything but a
    lab value.
    """

    if isinstance(answer, bool):
        interaction.remember(question, answer)
    elif isinstance(answer, (int, float)):
        interaction.remember(question, float(answer))
    else:
        interaction.remember(question, answer)


def run():

    janus.consult(REFERENCE_KB_PATH)

    scenarios = load_json(SCENARIOS_PATH)

    results = []
    correct = 0

    for scenario in scenarios:

        interaction.reset_all()

        for question, answer in scenario["answers"].items():
            _cache_answer(question, answer)

        error = None
        verdict = None

        try:
            outcome = janus.query_once("full_assessment(Result)")
            assessment = outcome.get("Result") if outcome else None
            verdict = assessment.get("verdict") if assessment else None
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
        "scope_caveat": (
            "This number tests internal consistency between reference_kb.pl "
            "and the Python verdict() function used to label these scenarios "
            "- both written by the same author from the same understanding "
            "of the ADA criteria. It does NOT test the actual LLM-generated "
            "knowledge bases the live app uses; see "
            "diagnostic_fresh_generation_check.json for that."
        ),
    })

    print(f"Diagnostic accuracy: {correct}/{total} ({accuracy:.0%})")

    for r in results:
        if not r["correct"]:
            print(
                f"  FAILED {r['id']} ({r['description']}): "
                f"expected={r['expected_verdict']} actual={r['actual_verdict']} "
                f"error={r['error']}"
            )


def _keyword_answer(question: str, pending, scenario: str):
    """
    Answers a pending question of an unknown, freshly-generated KB by
    keyword-matching its text, rather than by exact question-text
    lookup (which only works when the question wording is known in
    advance, as it is for the hand-written reference KB). `scenario`
    is "diabetic" or "normal" and controls which way lab values swing.
    """

    q = question.lower()
    modality = pending.modality
    options = pending.options

    # HbA1c is a percentage (~4-6.5% normal, >=6.5% diabetic) while
    # glucose readings are mg/dL (~70-100 normal, >=126-200 diabetic
    # depending on the specific test) - conflating the two units and
    # using one shared "normal"/"diabetic" numeric value for both
    # produced a false failure here once already: 85.0 is a normal
    # glucose reading but a medically nonsensical, and mathematically
    # diabetic, HbA1c percentage.
    is_hba1c = any(kw in q for kw in ("hba1c", "a1c"))
    is_glucose = "glucose" in q or "sugar" in q

    # Some generations ask which unit the patient is reporting in
    # before asking for the value itself. Always pick mg/dL when it's
    # offered, so every downstream numeric answer can stay in the one
    # unit system this function actually targets, rather than silently
    # answering an mg/dL-scaled number into an mmol/L question (85.0
    # mg/dL is normal; 85.0 mmol/L is off the charts).
    if "unit" in q and modality == "category" and options:
        for opt in options:
            if "mg" in str(opt).lower():
                return opt
        return options[0]

    # Safety net for when a fresh generation asks directly in mmol/L
    # without a separate unit-selection question: convert the intended
    # mg/dL target rather than answering a raw mg/dL-scaled number into
    # a mmol/L question, which would be wildly, wrongly elevated.
    is_mmol = "mmol" in q

    def _glucose_value(mg_dl: float) -> float:
        return round(mg_dl / 18.0, 1) if is_mmol else mg_dl

    if is_hba1c and modality in ("numeric", "range"):
        if scenario == "diabetic":
            return 9.0
        if scenario == "prediabetic":
            return 5.9  # squarely inside the 5.7-6.4 ADA increased-risk band
        return 5.2

    if is_glucose and modality in ("numeric", "range"):
        if "fasting" in q:
            if scenario == "diabetic":
                return _glucose_value(300.0)
            if scenario == "prediabetic":
                return _glucose_value(112.0)  # inside the 100-125 mg/dL prediabetes range
            return _glucose_value(85.0)
        # non-fasting (random/OGTT) readings: still unambiguous even in
        # the prediabetic scenario, since prediabetes here is defined
        # via fasting glucose specifically
        return _glucose_value(300.0) if scenario == "diabetic" else _glucose_value(85.0)

    if "fast" in q and modality in ("numeric", "range", "duration"):
        # Keep any fasting-window check satisfied (8-12h) rather than
        # accidentally invalidating the fasting-glucose criterion.
        return 10.0

    if modality == "boolean":
        return "no"

    if modality == "numeric":
        return 50.0

    if modality == "duration":
        return 5.0

    if modality == "range":
        lo = options.get("min", 0)
        hi = options.get("max", 10)
        return (lo + hi) / 2

    if modality == "category":
        return "none" if options and "none" in options else (options[0] if options else "none")

    if modality == "string":
        return "None."

    if modality == "multiple_category":
        return []

    if modality == "multi_structured_input":
        mode = options.get("mode", "sequence")
        if mode == "grouping":
            return {}
        return []

    if modality == "multi_attribute_entity":
        return {"entity": options.get("entity", "entity"), "data": {}}

    return "N/A"


def _run_fresh_scenario(question: str, scenario: str, snippet_name: str, max_turns: int = 40):
    """
    A genuine crash here (e.g. a fresh generation violating the Janus
    result-safety rule) must be recorded as a real failure, not allowed
    to propagate and kill the whole check silently - that already
    happened once during development of this function: an uncaught
    PrologError left a stale, misleading result file in place from an
    earlier run, because the crash prevented this function from ever
    reaching its own save_json call.
    """

    pipeline.reset_dialogue()
    interaction.reset_all()

    try:
        response = pipeline.ask(question, snippet_name=snippet_name)

        turns = 0
        while response.answer == "" and interaction.has_question():
            turns += 1
            if turns > max_turns:
                return {"outcome": "exceeded_max_turns", "answer": None, "error": None}
            pending = interaction.get_question()
            answer = _keyword_answer(pending.question, pending, scenario)
            response = pipeline.resume(answer)

        return {"outcome": "completed", "answer": response.answer, "error": None}

    except Exception as e:
        return {"outcome": "error", "answer": None, "error": str(e)}


def run_fresh_generation_check():
    """
    Generates a fresh knowledge base from the real diabetes.txt source
    text (the actual generator, not a hand-written stand-in), and
    drives it through the real interactive pipeline for two
    clinically unambiguous scenarios. This is a coarser, keyword-based
    check on the final natural-language answer rather than a
    structured verdict comparison, since a fresh generation's exact
    predicate names and question wording aren't known in advance - the
    trade-off accepted specifically to test the real generator instead
    of only the hand-written reference KB.
    """

    with open(FRESH_GEN_SNIPPET_TEXT_PATH, encoding="utf-8") as f:
        medical_text = f.read()

    kb_code = generate_prolog_kb(medical_text)

    kb_path = pipeline.kb_path_for(pipeline.DEFAULT_SNIPPET)
    kb_path.parent.mkdir(parents=True, exist_ok=True)
    kb_path.write_text(kb_code, encoding="utf-8")

    pipeline._loaded_snippet = None  # force this fresh generation to actually be consulted
    janus.consult(str(kb_path))
    pipeline._loaded_snippet = pipeline.DEFAULT_SNIPPET

    question = "Please run a full diagnostic workup including symptoms, severity, duration, and current medications."

    # Three scenarios, not two easy extremes: an unambiguous positive,
    # an unambiguous negative, AND a genuinely ambiguous middle case
    # (fasting glucose 112 mg/dL / HbA1c 5.9%, squarely in ADA
    # prediabetes/increased-risk territory) - the two-scenario version
    # of this check only ever exercised the cases a reasonable system
    # could hardly get wrong, which is not a meaningful stress test.
    results = {}
    for scenario in ("diabetic", "prediabetic", "normal"):
        outcome = _run_fresh_scenario(question, scenario, pipeline.DEFAULT_SNIPPET)
        results[scenario] = outcome
        print(f"Fresh generation check ({scenario}): {outcome}")

    # Free text can express the same underlying meaning in more ways
    # than any fixed keyword list can enumerate ("short of diabetes",
    # "low clinical risk", "not yet diabetic", ...). Rather than
    # chasing every negation phrasing individually - which turned into
    # exactly the kind of whack-a-mole this project has hit before with
    # substring matching - this uses direct positive-evidence checks
    # (does the answer name the expected condition at all) plus a
    # proximity-based check instead of exact substrings, and is upfront
    # that this remains an inherently less rigorous check than the
    # structured Verdict comparison run() does against the reference
    # KB; it is a real-generator smoke test, not a precision benchmark.
    def _normalize(text: str) -> str:
        return text.lower().replace("-", " ").replace("_", " ")

    def _mentions_prediabetes(text: str) -> bool:
        return "prediabetes" in text or "pre diabetes" in text

    def _mentions_bare_diabetes(text: str) -> bool:
        """
        True if `text` claims outright diabetes, treated as reliable
        only when prediabetes is NOT also mentioned - if both appear,
        the bare "diabetes" is almost certainly part of a comparative
        phrase like "short of diabetes" rather than a separate,
        contradictory claim.
        """
        if _mentions_prediabetes(text):
            return False
        stripped = text.replace("prediabetes", "").replace("pre diabetes", "")
        return "diabetes" in stripped

    def _mentions_low_or_no_risk(text: str) -> bool:
        """Proximity match: "low" within a few words of "risk", e.g.
        "low risk", "low clinical risk", "low overall risk" all match,
        not only the exact phrase "low risk"."""
        import re as _re
        if _re.search(r"\blow\b(?:\s+\w+){0,3}\s+\brisk\b", text):
            return True
        if "no risk" in text:
            return True
        if "routine monitoring" in text or "not indicated" in text:
            return True
        return False

    diabetic_answer = _normalize(results["diabetic"].get("answer") or "")
    prediabetic_answer = _normalize(results["prediabetic"].get("answer") or "")
    normal_answer = _normalize(results["normal"].get("answer") or "")

    diabetic_correct = (
        results["diabetic"]["outcome"] == "completed"
        and _mentions_bare_diabetes(diabetic_answer)
    )

    # The ambiguous case is scored more leniently on purpose: the only
    # genuine failure is claiming outright diabetes, or claiming a
    # fully clean/no-risk result - naming prediabetes, borderline
    # status, or increased risk are all acceptable characterizations
    # of a value that is legitimately in that gray zone.
    prediabetic_correct = (
        results["prediabetic"]["outcome"] == "completed"
        and not _mentions_bare_diabetes(prediabetic_answer)
        and not (
            _mentions_low_or_no_risk(prediabetic_answer)
            and not _mentions_prediabetes(prediabetic_answer)
        )
    )

    normal_correct = (
        results["normal"]["outcome"] == "completed"
        and not _mentions_bare_diabetes(normal_answer)
        and _mentions_low_or_no_risk(normal_answer)
    )

    summary = {
        "diabetic_scenario_correct": diabetic_correct,
        "prediabetic_scenario_correct": prediabetic_correct,
        "normal_scenario_correct": normal_correct,
        "diabetic_outcome": results["diabetic"]["outcome"],
        "prediabetic_outcome": results["prediabetic"]["outcome"],
        "normal_outcome": results["normal"]["outcome"],
        "diabetic_answer": results["diabetic"].get("answer"),
        "prediabetic_answer": results["prediabetic"].get("answer"),
        "normal_answer": results["normal"].get("answer"),
        "diabetic_error": results["diabetic"].get("error"),
        "prediabetic_error": results["prediabetic"].get("error"),
        "normal_error": results["normal"].get("error"),
    }

    save_json("evaluation/results/diagnostic_fresh_generation_check.json", summary)

    print(f"Fresh-generation diabetic scenario correct: {diabetic_correct}")
    print(f"Fresh-generation prediabetic (ambiguous) scenario correct: {prediabetic_correct}")
    print(f"Fresh-generation normal scenario correct: {normal_correct}")

    return summary


if __name__ == "__main__":
    run()
    run_fresh_generation_check()
