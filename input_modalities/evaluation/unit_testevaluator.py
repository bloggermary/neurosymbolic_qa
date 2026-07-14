import sys
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler
from modalities.category_handler import CategoryHandler
from modalities.range_handler import RangeHandler
from modalities.duration_handler import DurationHandler


BASE_DIR = Path(__file__).resolve().parent.parent

TEST_PATH = BASE_DIR / "evaluation" / "unit_test.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_handler(handler_type: str):
    handlers = {
        "boolean": BooleanHandler(),
        "numeric": NumericHandler(),
        "string": StringHandler(),
        "category": CategoryHandler(),
        "range": RangeHandler(),
        "duration": DurationHandler(),
    }

    return handlers.get(handler_type)


def execute_handler(handler, case):

    handler_type = case["handler"]

    if handler_type == "boolean":
        return handler.handle(case["question"])

    elif handler_type == "numeric":
        return handler.handle(case["question"])

    elif handler_type == "string":
        return handler.handle(case["question"])

    elif handler_type == "duration":
        return handler.handle(case["question"])

    elif handler_type == "range":
        return handler.handle(
            case["question"],
            case["start"],
            case["stop"],
        )

    elif handler_type == "category":
        return handler.handle(
            case["question"],
            case["categories"],
        )

    else:
        raise ValueError(f"Unknown handler: {handler_type}")


def evaluate():

    test_cases = load_json(TEST_PATH)

    total = len(test_cases)
    passed = 0

    print("\n==========================")
    print("Handler Evaluation")
    print("==========================")

    for case in test_cases:

        print(f"\nTest: {case['id']}")

        handler = create_handler(case["handler"])

        if handler is None:
            print(f"Unknown handler: {case['handler']}")
            continue

        with patch(
            "builtins.input",
            return_value=str(case["user_input"])
        ):

            try:
                result = execute_handler(handler, case)

                success = result == case["expected_output"]

            except Exception as e:

                result = str(e)
                success = False

        print(f"Question: {case['question']}")
        print(f"Input: {case['user_input']}")
        print(f"Expected: {case['expected_output']}")
        print(f"Actual: {result}")

        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")

    print("\n==========================")
    print("Overall")
    print("==========================")
    print(f"Passed: {passed}/{total}")
    print(f"Accuracy: {passed / total:.2%}")


if __name__ == "__main__":
    evaluate()