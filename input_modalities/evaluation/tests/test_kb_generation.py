"""
KB generation evaluation.

Runs the current kb_generator.py against every medical text in
data/snippets/ (not a separate hand-written fixture - the snippets
themselves ARE the input domain this generator has to handle) and
checks two kinds of properties:

1. Universal structural requirements every generated KB must satisfy
   regardless of domain (diagnose/1 and the three verdict predicates
   are defined, it's valid enough Prolog to consult).
2. Regressions against specific bug classes seen before (orphaned
   "ask_" prefixed fact predicates, placeholder/dummy clauses).
"""

import re
from pathlib import Path

import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from evaluation.testing_suite.metrics import save_json, compute_accuracy


SNIPPETS_DIR = Path("data/snippets")

REQUIRED_PREDICATES = ["diagnose", "diabetes", "prediabetes", "low_risk"]

FORBIDDEN_PATTERNS = [
    "ensure predicate",
    "ensure ask_",
]


def _defines_predicate(kb_code: str, predicate: str) -> bool:
    """
    True if `predicate` appears as a clause head, either as a fact/rule
    written with parens (diagnose(X) :- ...) or with none (diabetes :- ...).
    """

    pattern = rf"\b{re.escape(predicate)}\b\s*(\(|:-|\.)"

    return re.search(pattern, kb_code) is not None


def _consults_cleanly(kb_code: str, tmp_path: Path) -> tuple[bool, str]:

    tmp_path.write_text(kb_code, encoding="utf-8")

    try:
        janus.consult(str(tmp_path))
        return True, ""
    except Exception as error:
        return False, str(error)


def run():

    snippet_paths = sorted(SNIPPETS_DIR.glob("*.txt"))

    results = []
    passed = 0

    tmp_path = Path("prolog/generated_kb/_kb_generation_eval_tmp.pl")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    for snippet_path in snippet_paths:

        name = snippet_path.stem
        text = snippet_path.read_text(encoding="utf-8")

        kb_code = generate_prolog_kb(text)

        missing_predicates = [
            p for p in REQUIRED_PREDICATES
            if not _defines_predicate(kb_code, p)
        ]

        forbidden_found = [
            pattern for pattern in FORBIDDEN_PATTERNS
            if pattern in kb_code
        ]

        consults_ok, consult_error = _consults_cleanly(kb_code, tmp_path)

        success = (
            not missing_predicates
            and not forbidden_found
            and consults_ok
        )

        results.append({
            "snippet": name,
            "missing_predicates": missing_predicates,
            "forbidden_patterns_found": forbidden_found,
            "consults_cleanly": consults_ok,
            "consult_error": consult_error,
            "success": success,
        })

        if success:
            passed += 1

    tmp_path.unlink(missing_ok=True)

    total = len(results)
    accuracy = compute_accuracy(passed, total)

    save_json("evaluation/results/kb_results.json", results)
    save_json("evaluation/results/kb_accuracy.json", {
        "total": total,
        "passed": passed,
        "accuracy": accuracy,
    })

    print(f"KB generation: {passed}/{total} passed ({accuracy:.0%})")

    for r in results:
        if not r["success"]:
            print(f"  FAILED {r['snippet']}: "
                  f"missing={r['missing_predicates']} "
                  f"forbidden={r['forbidden_patterns_found']} "
                  f"consult_error={r['consult_error'][:100]}")


if __name__ == "__main__":
    run()
