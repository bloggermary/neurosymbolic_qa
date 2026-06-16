import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

from llm.query_generator import generate_query

KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"
TEST_PATH = "evaluation/test_questions.json"

with open(KB_PATH, "r", encoding="utf-8") as f:
    prolog_code = f.read()

with open(TEST_PATH, "r", encoding="utf-8") as f:
    test_cases = json.load(f)

passed = 0
total = len(test_cases)

for case in test_cases:

    success = True

    question = case["question"]
    query = generate_query(question, prolog_code)

    print(f"\nQuestion: {question}")
    print(f"Generated query: {query}")

    for text in case.get("expected_query_contains", []):
        if text not in query:
            print(f"Missing: {text}")
            success = False

    for text in case.get("must_not_contain", []):
        if text in query:
            print(f"Forbidden: {text}")
            success = False

    if success:
        print("PASS")
        passed += 1
    else:
        print("FAIL")

print("\n==========================")
print(f"Passed: {passed}/{total}")
print(f"Accuracy: {passed/total*100:.1f}%")
print("==========================")