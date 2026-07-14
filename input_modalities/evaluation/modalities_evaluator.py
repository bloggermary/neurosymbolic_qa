import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import janus_swi as janus
import main
from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm.client import client
from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_PATH = BASE_DIR / "evaluation" / "test_modalities.json"
EVAL_KB_PATH = BASE_DIR / "prolog" / "generated_kb" / "evaluation_kb.pl"
DEFAULT_SOURCE_FILE = "data/snippets/diabetes.txt"
TEST_GENERATOR_MODEL = "gpt-5-mini"

# ================================================================
# Structured-output schema for generated evaluation cases
# ================================================================

Modality = Literal[
    "boolean",
    "numeric",
    "string",
    "category",
    "range",
    "duration",
]

class ExpectedFollowup(BaseModel):
    """One expected Prolog -> Python follow-up interaction."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        description="Stable lowercase snake_case semantic key used in ask_*()."
    )
    question: str = Field(description="Expected meaning of the follow-up question.")
    modality: Modality
    answer: str = Field(
        description="Simulated user answer. Numeric answers are also stored as strings."
    )

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
            raise ValueError("key must be a lowercase snake_case identifier")
        return value

class EvaluationCase(BaseModel):
    """One end-to-end behavioural evaluation case."""

    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    source_file: str
    expected_followups: list[ExpectedFollowup]
    max_followups: int = Field(ge=0)
    correct_answer: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
            raise ValueError("id must be a lowercase snake_case identifier")
        return value

class EvaluationSuite(BaseModel):
    """Schema returned by OpenAI Structured Outputs."""

    model_config = ConfigDict(extra="forbid")

    tests: list[EvaluationCase] = Field(min_length=9, max_length=12)

TEST_GENERATOR_INSTRUCTIONS = """
You generate behavioural evaluation cases for a neurosymbolic
medical question-answering system.

You receive:

1. the original medical source text,
2. the generated SWI-Prolog knowledge base.

The generated Prolog knowledge base is the source of truth for:

- available predicates,
- ask_* calls,
- semantic keys,
- question modalities,
- category values,
- range bounds,
- possible execution paths.

CRITICAL KEY RULES:

- Every expected follow-up key must exactly match a concrete key
  appearing in an ask_* call in the provided Prolog knowledge base.
- Copy keys character-for-character from the Prolog code.
- Never shorten, rename, normalize, paraphrase, or invent keys.

- Do not generate an expected follow-up that does not exist in the
  provided Prolog knowledge base.
- Do not generate a duration follow-up unless the Prolog knowledge
  base actually calls ask_duration/3.
- Numeric and duration answers must contain only the numeric value,
  for example "210", "6.5", or "10".
- Do not write units inside answer values, such as "10 hours".
- Units belong only in the question field.
- Generate test cases that correspond to real execution paths of
  the provided Prolog rules.
- For a minimal positive case, provide a value that should make the
  earliest sufficient criterion succeed and stop further questions.
- expected_followups must list every question that Prolog is expected
  to ask on that execution path, and no others.
- The question field must contain a natural user question, not a test
  scenario description.
- Do not reveal expected values, execution order, or the expected diagnosis
  in the question field.  
"""

# ================================================================
# General helpers
# ================================================================

def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value: str) -> str:
    return value.strip().lower()

# ================================================================
# generate test_modalities.json with Structured Outputs
# ================================================================

def generate_testcases(
    source_file: str,
    prolog_code: str,
    output_path: Path = TEST_PATH,
) -> list[dict]:
    """
    Generate schema-valid behavioural test cases and write them directly to
    evaluation/test_modalities.json.

    This function creates test specifications only. Pass/fail decisions and
    metrics are still computed deterministically by evaluate().
    """
    source_path = BASE_DIR / source_file

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    medical_text = load_text(source_path)

    response = client.responses.parse(
    model=TEST_GENERATOR_MODEL,
    instructions=TEST_GENERATOR_INSTRUCTIONS,
    input=(
        f"source_file:\n{source_file}\n\n"
        f"Medical source text:\n{medical_text}\n\n"
        f"Generated Prolog knowledge base:\n"
        f"{prolog_code}"
    ),
    text_format=EvaluationSuite,
)

    suite = response.output_parsed
    if suite is None:
        raise RuntimeError("OpenAI returned no parsed evaluation suite.")

    test_cases: list[dict] = []
    for test in suite.tests:
        data = test.model_dump()

        # The local application, not the model, controls the file path.
        data["source_file"] = source_file
        test_cases.append(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(test_cases, file, ensure_ascii=False, indent=2)

    print("\n==========================")
    print("Structured test generation")
    print("==========================")
    print(f"Generated tests: {len(test_cases)}")
    print(f"Source: {source_file}")
    print(f"Saved to: {output_path}")

    return test_cases

# ================================================================
# Evaluation session: supplies simulated answers to Prolog callbacks
# ================================================================

class EvalSession:
    def __init__(self, expected_followups):
        self.expected_followups = expected_followups
        self.actual_followups = []
        self.answer_cache = {}

    def record_followup(self, followup: dict):
        self.actual_followups.append(followup)

    def _find_expected_by_key(self, key: str):
        key = str(key)

        for expected in self.expected_followups:
            if str(expected.get("key")) == key:
                return expected

        return None

    def ask_boolean(self, key: str, question: str) -> bool:
        key = str(key)

        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "boolean",
        })

        expected = self._find_expected_by_key(key)
        if expected is None:
            return False
        else: 
            answer = normalize(str(expected.get("answer", "no")))
            value = answer in {"yes", "ja", "true", "1"}
        self.answer_cache[key] = value
        return value

    def ask_numeric(self, key: str, question: str) -> float:
        key = str(key)
        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "numeric",
        })

        expected = self._find_expected_by_key(key)
        if expected is None:
            return 0.0
        else:
            value = float(str(expected["answer"]).replace(",", "."))
        self.answer_cache[key] = value
        return value

    def ask_string(self, key: str, question: str) -> str:
        key = str(key)

        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "string",
        })

        expected = self._find_expected_by_key(key)
        if expected is None:
            value = ""
        else:
            value = str(expected["answer"])
        self.answer_cache[key] = value
        return value

    def ask_duration(self, key: str, question: str) -> int:
        key = str(key)

        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "duration",
        })

        expected = self._find_expected_by_key(key)
        if expected is None:
            value = 0
        else:
            value = int(expected["answer"])
        self.answer_cache[key] = value
        return value

    def ask_range(self, key: str, question: str, start: int, stop: int) -> int:
        key = str(key)
        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "range",
        })

        expected = self._find_expected_by_key(key)
        if expected is None:
            value = start
        else:
            answer = int(expected["answer"])
            if not start <= answer <= stop:
                raise ValueError(
                    f"Test answer {answer} for key {key!r} is outside {start}..{stop}."
                )
            value = answer
        self.answer_cache[key] = value
        return value

    def ask_category(self, key: str, question: str, categories: list[str]) -> str:
        key = str(key)
        if key in self.answer_cache:
            return self.answer_cache[key]

        self.record_followup({
            "key": str(key),
            "question": question,
            "modality": "category",
        })

        expected = self._find_expected_by_key(key)
        normalized_categories = [normalize(str(category)) for category in categories]

        if expected is None:
            value = normalized_categories[0]
        else:
            value = normalize(str(expected["answer"]))

        if value not in normalized_categories:
            raise ValueError(
                f"Test answer {value!r} for key {key!r} is not in {categories}."
            )
        self.answer_cache[key] = value
        return value

def patch_main_callbacks(session: EvalSession):
    main.ask_boolean = session.ask_boolean
    main.ask_numeric = session.ask_numeric
    main.ask_string = session.ask_string
    main.ask_duration = session.ask_duration
    main.ask_range = session.ask_range
    main.ask_category = session.ask_category

# ================================================================
# Existing end-to-end evaluation
# ================================================================

def generate_eval_kb(source_file: str) -> str:
    source_path = BASE_DIR / source_file
    medical_text = load_text(source_path)

    prolog_code = generate_prolog_kb(medical_text)

    EVAL_KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVAL_KB_PATH.open("w", encoding="utf-8") as file:
        file.write(prolog_code)

    return prolog_code

def run_reasoning(query: str):
    query = query.strip().rstrip(".")
    return janus.query_once(query)

def normalize_generated_query(query: str | None) -> str:
    """
    Normalize an LLM-generated Prolog query.

    Removes markdown fences, ?-, trailing periods, and surrounding whitespace.
    """
    if query is None:
        return ""

    normalized = str(query).strip()

    # Remove possible markdown code fences.
    normalized = normalized.replace("```prolog", "")
    normalized = normalized.replace("```", "")
    normalized = normalized.strip()

    # Remove the interactive Prolog prefix.
    if normalized.startswith("?-"):
        normalized = normalized[2:].strip()

    # Remove final period because janus.query_once expects the goal itself.
    normalized = normalized.rstrip(".").strip()

    return normalized

def generate_query_with_fallback(
    question: str,
    prolog_code: str,
) -> str:
    """
    Generate a Prolog query with a deterministic fallback.

    If the LLM incorrectly returns 'fail', but the generated knowledge base
    contains diagnose/1, use diagnose(Result). This prevents a query-generation
    failure from blocking the whole end-to-end evaluation.
    """
    raw_query = generate_query(
        question,
        prolog_code,
    )

    query = normalize_generated_query(raw_query)

    if not query or query == "fail":
        query_valid = False
        result = {"truth": False}
    else:
        query_valid = True
        result = run_reasoning(query)

    # Check whether the actual generated KB defines diagnose/1.
    diagnose_exists = re.search(
        r"(?m)^\s*diagnose\s*\([^)]*\)\s*(?::-|\.)",
        prolog_code,
    )

    if diagnose_exists:
        print(
            "[Query fallback] LLM returned 'fail', but diagnose/1 "
            "exists in the generated KB. Using diagnose(Result)."
        )
        return "diagnose(Result)"

    print(
        "[Query fallback] LLM returned 'fail' and no diagnose/1 "
        "predicate was found in the generated KB."
    )

    return "fail"

def resolve_evaluation_query(prolog_code: str) -> str:
    """
    Resolve the top-level diagnosis query directly from the generated KB.

    For modality evaluation, the query must remain constant across test
    scenarios. The scenario is represented by simulated follow-up answers,
    not by changing the Prolog goal.
    """

    # Preferred top-level predicate for the current KB design.
    diagnose_match = re.search(
        r"(?m)^\s*diagnose\s*\([^)]*\)\s*(?::-|\.)",
        prolog_code,
    )

    if diagnose_match:
        return "diagnose(Result)"

    # Optional fallback for KBs using diagnosis/1 instead.
    diagnosis_match = re.search(
        r"(?m)^\s*diagnosis\s*\([^)]*\)\s*(?::-|\.)",
        prolog_code,
    )

    if diagnosis_match:
        return "diagnosis(Result)"

    return "fail"

def evaluate_followups(expected_followups, actual_followups):
    expected_by_key = {
        str(f["key"]): f
        for f in expected_followups
        if "key" in f
    }

    actual_by_key = {
        str(f["key"]): f
        for f in actual_followups
        if "key" in f
    }

    expected_keys = set(expected_by_key)
    actual_keys = set(actual_by_key)

    if not expected_keys:
        return 1.0, 1.0

    matched_keys = expected_keys & actual_keys
    followup_recall = len(matched_keys) / len(expected_keys)

    modality_matches = sum(
        expected_by_key[key]["modality"] == actual_by_key[key]["modality"]
        for key in matched_keys
    )
    modality_accuracy = modality_matches / len(expected_keys)

    return followup_recall, modality_accuracy

def evaluate_answer(result: dict, correct_answer: str) -> bool:
    expected = normalize(str(correct_answer))

    if "Result" in result:
        actual = normalize(str(result["Result"]))
        return actual == expected

    truth_value = result.get("truth")

    if expected in {"yes", "true"}:
        return truth_value is True

    if expected in {"no", "false"}:
        return truth_value is False

    return False

def validate_test_cases(test_cases: list[dict]) -> None:
    """Validate loaded JSON before starting expensive KB/LLM calls."""
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError("The test file must contain a non-empty JSON list.")

    required_case_fields = {
        "id",
        "question",
        "source_file",
        "expected_followups",
        "correct_answer",
    }

    for index, case in enumerate(test_cases):
        missing = required_case_fields - set(case)
        if missing:
            raise ValueError(
                f"Test case at index {index} is missing fields: {sorted(missing)}"
            )

        for followup_index, followup in enumerate(case["expected_followups"]):
            missing_followup = {
                "key",
                "question",
                "modality",
                "answer",
            } - set(followup)

            if missing_followup:
                raise ValueError(
                    f"Test {case['id']!r}, follow-up {followup_index} is missing: "
                    f"{sorted(missing_followup)}"
                )

def evaluate(
    test_path: Path = TEST_PATH,
    prolog_code: str | None = None,
):
    """
    Execute all behavioural test cases against one fixed Prolog KB.

    The evaluator uses one deterministic diagnosis query for the modality
    evaluation. This prevents scenario descriptions in generated test
    questions from producing overly specific queries such as
    diagnose(no_diabetes_detected).
    """
    test_cases = load_json(test_path)
    validate_test_cases(test_cases)

    if not test_cases:
        raise ValueError("No test cases found.")

    # ------------------------------------------------------------
    # 1. All generated tests must use the same source file
    # ------------------------------------------------------------
    source_files = {
        case["source_file"]
        for case in test_cases
    }

    if len(source_files) != 1:
        raise ValueError(
            "This evaluator expects one source_file per evaluation run, "
            f"but found: {sorted(source_files)}"
        )

    source_file = next(iter(source_files))

    # ------------------------------------------------------------
    # 2. Generate the KB only once
    # ------------------------------------------------------------
    if prolog_code is None:
        prolog_code = generate_eval_kb(source_file)

    janus.consult(str(EVAL_KB_PATH))


    total = len(test_cases)

    sum_query_validity = 0.0
    sum_followup_recall = 0.0
    sum_modality_accuracy = 0.0
    sum_answer_accuracy = 0.0
    sum_efficiency = 0.0

    # ------------------------------------------------------------
    # 4. Run every test independently
    # ------------------------------------------------------------
    for case in test_cases:
        print("\n==========================")
        print(f"Test: {case['id']}")
        print(f"Question: {case['question']}")

        expected_followups = case.get(
            "expected_followups",
            [],
        )

        max_followups = case.get(
            "max_followups",
            len(expected_followups),
        )

        # Each test receives a fresh simulated answer session.
        session = EvalSession(expected_followups)
        patch_main_callbacks(session)

        raw_query = generate_query(
            case["question"],
            prolog_code,
        )

        query = normalize_generated_query(raw_query)

        query_valid = bool(query) and query != "fail"

        print(f"Correct answer: {case['correct_answer']}")
        print(f"Generated query: {query}")

        if not query_valid:
            print(
                "Query resolution failed: no executable diagnosis "
                "predicate was found."
            )
            result = {"truth": False}

        else:
            try:
                result = run_reasoning(query)

            except Exception as error:
                print(f"Prolog execution error: {error}")
                result = {"truth": False}
                query_valid = False

        actual_followups = session.actual_followups

        followup_recall, modality_accuracy = evaluate_followups(
            expected_followups,
            actual_followups,
        )

        # Query or Prolog errors must never count as correct negatives.
        if query_valid:
            answer_correct = evaluate_answer(
                result,
                case["correct_answer"],
            )
        else:
            answer_correct = False

        answer_accuracy = (
            1.0 if answer_correct else 0.0
        )

        actual_count = len(actual_followups)

        unnecessary_followups = max(
            0,
            actual_count - max_followups,
        )

        if actual_count == 0:
            efficiency_score = (
                1.0
                if max_followups == 0 and query_valid
                else 0.0
            )
        else:
            efficiency_score = min(
                1.0,
                max_followups / actual_count,
            )

        query_validity = (
            1.0 if query_valid else 0.0
        )

        sum_query_validity += query_validity
        sum_followup_recall += followup_recall
        sum_modality_accuracy += modality_accuracy
        sum_answer_accuracy += answer_accuracy
        sum_efficiency += efficiency_score

        print("\nExpected followups:")
        if expected_followups:
            for followup in expected_followups:
                print(
                    f"- {followup['key']}: "
                    f"{followup['question']} "
                    f"[{followup['modality']}] "
                    f"-> {followup['answer']}"
                )
        else:
            print("- None")

        print("\nActual followups:")
        if actual_followups:
            for followup in actual_followups:
                print(
                    f"- {followup['key']}: "
                    f"{followup['question']} "
                    f"[{followup['modality']}]"
                )
        else:
            print("- None")

        print("\nMetrics:")
        print(f"Query valid: {query_valid}")
        print(f"Follow-up recall: {followup_recall:.2f}")
        print(f"Modality accuracy: {modality_accuracy:.2f}")
        print(f"Answer accuracy: {answer_accuracy:.2f}")
        print(f"Efficiency score: {efficiency_score:.2f}")
        print(f"Unnecessary followups: {unnecessary_followups}")
        print(f"Raw result: {result}")

    print("\n==========================")
    print("Overall results")
    print("==========================")
    print(
        f"Query validity: "
        f"{sum_query_validity / total:.2f}"
    )
    print(
        f"Follow-up recall: "
        f"{sum_followup_recall / total:.2f}"
    )
    print(
        f"Modality accuracy: "
        f"{sum_modality_accuracy / total:.2f}"
    )
    print(
        f"Answer accuracy: "
        f"{sum_answer_accuracy / total:.2f}"
    )
    print(
        f"Efficiency score: "
        f"{sum_efficiency / total:.2f}"
    )
    
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Optionally generate test_modalities.json using OpenAI Structured "
            "Outputs, then run the existing end-to-end evaluation."
        )
    )
    parser.add_argument(
        "--generate-tests",
        action="store_true",
        help="Generate and overwrite evaluation/test_modalities.json first.",
    )
    parser.add_argument(
        "--source-file",
        default=DEFAULT_SOURCE_FILE,
        help=(
            "Project-relative medical source file used for test generation. "
            f"Default: {DEFAULT_SOURCE_FILE}"
        ),
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate test_modalities.json without running the evaluator.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # 이번 실행에서 사용할 동일한 Prolog KB
    prolog_code = None

    if args.generate_tests or args.generate_only:
        # 1. KB를 딱 한 번 생성
        prolog_code = generate_eval_kb(
            args.source_file
        )

        # 2. 바로 그 동일한 KB를 바탕으로 테스트 생성
        generate_testcases(
            source_file=args.source_file,
            prolog_code=prolog_code,
        )

    if not args.generate_only:
        # 3. 테스트 생성 때 사용한 동일한 KB로 평가
        # 생성 옵션 없이 실행했다면 evaluate() 내부에서 한 번 생성
        evaluate(
            prolog_code=prolog_code,
        )