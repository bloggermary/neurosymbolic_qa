import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.query_generator import generate_query


BASE_DIR = Path(__file__).resolve().parent.parent

KB_PATH = BASE_DIR / "prolog" / "generated_kb" / "diabetes_diagnosis.pl"
TEST_PATH = BASE_DIR / "evaluation" / "test_modalities.json"


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate():
    prolog_code = load_text(KB_PATH)
    test_cases = load_json(TEST_PATH)

    passed = 0
    total = len(test_cases)

    for case in test_cases:
        success = True

        question = case["question"]
        query = generate_query(question, prolog_code)

        print(f"\nTest: {case['id']}")
        print(f"Question: {question}")
        print(f"Generated query: {query}")

        for text in case.get("expected_query_contains", []):
            if text not in query:
                print(f"Missing expected text: {text}")
                success = False

        for text in case.get("must_not_contain", []):
            if text in query:
                print(f"Forbidden text found: {text}")
                success = False

        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")

    print("\n==========================")
    print(f"Passed: {passed}/{total}")
    print(f"Accuracy: {passed / total * 100:.1f}%")
    print("==========================")


if __name__ == "__main__":
    evaluate()