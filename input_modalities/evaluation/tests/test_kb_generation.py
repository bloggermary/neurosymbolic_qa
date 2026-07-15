import sys
from pathlib import Path
import json
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from input_modalities.llm.kb_generator import generate_prolog_kb


BASE_DIR = Path(__file__).resolve().parent.parent

KB_PATH = BASE_DIR / "prolog" / "generated_kb" / "diabetes_diagnosis.pl"
TEST_PATH = BASE_DIR / "evaluation" / "tests" / "json_entries" / "test_kb_generation.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_predicates(prolog_code: str):
    """
    Extracts predicate names from Prolog code.
    Example: diabetes(patient) -> diabetes
    """
    matches = re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", prolog_code)
    return set(matches)


def evaluate():
    test_cases = load_json(TEST_PATH)

    passed = 0
    total = len(test_cases)

    print("\n================ KB GENERATION EVALUATION ================\n")

    for case in test_cases:
        input_text = case["input_text"]

        # Generate KB from model
        kb_code = generate_prolog_kb(input_text)

        predicates = extract_predicates(kb_code)

        success = True

        print(f"\nTest ID: {case['id']}")
        print(f"Input: {input_text}")

        # --- Check expected predicates ---
        for p in case.get("expected_predicates", []):
            if p not in predicates:
                print(f"Missing predicate: {p}")
                success = False

        # --- Check expected rules (simple substring check) ---
        for rule in case.get("expected_rules", []):
            if rule not in kb_code:
                print(f"Missing rule/threshold: {rule}")
                success = False

        # --- Check forbidden patterns ---
        for bad in case.get("must_not_contain", []):
            if bad in kb_code:
                print(f"Forbidden content found: {bad}")
                success = False

        if success:
            print("RESULT: PASS")
            passed += 1
        else:
            print("RESULT: FAIL")

    print("\n================ SUMMARY ================\n")
    print(f"Passed: {passed}/{total}")
    print(f"Accuracy: {(passed / total) * 100:.2f}%")
    print("\n========================================\n")


if __name__ == "__main__":
    evaluate()