import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modalities.router import route_boolean, route_numeric, route_string


TEST_PATH = "evaluation/test_modalities.json"


def run_case(case):
    inputs = iter(case["inputs"])

    def fake_input(prompt):
        try:
            return next(inputs)
        except StopIteration:
            raise RuntimeError("No valid input provided")

    try:
        with patch("builtins.input", fake_input):
            if case["modality"] == "boolean":
                answer = route_boolean(case["question"])
            elif case["modality"] == "numeric":
                answer = route_numeric(case["question"])
            elif case["modality"] == "string":
                answer = route_string(case["question"])
            else:
                raise ValueError(f"Unknown modality: {case['modality']}")

        if case.get("expected_valid") is False:
            return False, f"Expected invalid, but got valid answer: {answer}"

        expected = case.get("expected_answer")
        return answer == expected, answer

    except Exception as e:
        if case.get("expected_valid") is False:
            expected_error = case.get("expected_error", "")
            return expected_error in str(e), str(e)

        return False, str(e)


def main():
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    passed = 0

    for case in test_cases:
        success, result = run_case(case)

        print(f"\nTest: {case['id']}")
        print(f"Modality: {case['modality']}")
        print(f"Inputs: {case['inputs']}")
        print(f"Expected: {case.get('expected_answer', case.get('expected_error'))}")
        print(f"Actual: {result}")

        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")

    print("\n==========================")
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Accuracy: {passed / len(test_cases) * 100:.1f}%")
    print("==========================")


if __name__ == "__main__":
    main()