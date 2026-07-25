"""
End-to-end modality evaluator

It preserves the evaluator's console format and metrics:
- query validity
- follow-up recall
- modality accuracy
- answer accuracy
- efficiency score
- unnecessary follow-ups

"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import janus_swi as janus
from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm.client import client
from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from services.interaction_service import interaction


BASE_DIR = Path(__file__).resolve().parent.parent
TEST_PATH = BASE_DIR / "evaluation" / "test_modalities.json"
EVAL_KB_PATH = BASE_DIR / "prolog" / "generated_kb" / "evaluation_kb.pl"
RESULTS_DIR = BASE_DIR / "evaluation" / "results"
RESULTS_PATH = RESULTS_DIR / "modalities_evaluation_results.json"
SUMMARY_PATH = RESULTS_DIR / "modalities_evaluation_summary.json"
DEFAULT_SOURCE_FILE = "data/snippets/diabetes.txt"
TEST_GENERATOR_MODEL = "gpt-5-mini"
MAX_REASONING_STEPS = 50


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
    "multiple_category",
    "multi_structured_input",
    "multi_attribute_entity",
]

class ExpectedFollowup(BaseModel):
    """One expected Prolog -> Python follow-up interaction."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        description=(
            "Stable lowercase snake_case semantic identifier for evaluation. "
            "The current runtime identifies cached answers by question text."
        )
    )
    question: str = Field(description="Expected meaning/wording of the follow-up.")
    modality: Modality
    answer: Any = Field(description="Simulated user answer for this follow-up.")

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
    model_config = ConfigDict(extra="forbid")

    canonical_question: str = Field(
        min_length=1,
        description=(
            "One broad end-to-end diagnosis question used for every test case."
        ),
    )

    tests: list[EvaluationCase] = Field(
        min_length=1,
        description="Generated end-to-end evaluation test cases.",
    )

TEST_GENERATOR_INSTRUCTIONS = """
You generate behavioural evaluation cases for a neurosymbolic medical
question-answering system.

You receive the medical source text and the generated SWI-Prolog knowledge
base. The generated knowledge base is the source of truth for reachable
ask_* calls, question wording, modalities, categories, range bounds, and
possible execution paths.

The current KB uses ask_* predicates whose first relevant argument is the
natural-language question. It does NOT provide a separate semantic key.
Therefore:
- create a stable lowercase snake_case key from the medical meaning of each
  expected question;
- keep that key consistent inside the test file;
- copy or closely preserve the actual question wording from the KB;
- never invent a follow-up that cannot be reached in the KB;
- expected_followups must contain every question expected on that execution
  path and no others;
- numeric, range, and duration answers must be numeric values without units;
- boolean answers should be yes/no;
- category answers must be one of the KB categories;
- multiple_category answers must be a JSON list;
- multi_structured_input and multi_attribute_entity answers must use the
  JSON-safe structure expected by the corresponding ask_* call;
- the user question must be natural and must not reveal the expected answers.
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


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def normalize(value: Any) -> str:
    return str(value).strip().lower()


def normalize_question(value: Any) -> str:
    text = normalize(value)
    text = re.sub(r"[^a-z0-9.%]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def question_similarity(left: str, right: str) -> float:
    left_normalized = normalize_question(left)
    right_normalized = normalize_question(right)

    if not left_normalized or not right_normalized:
        return 0.0

    sequence_score = SequenceMatcher(
        None,
        left_normalized,
        right_normalized,
    ).ratio()

    left_tokens = set(left_normalized.split())
    right_tokens = set(right_normalized.split())

    union = left_tokens | right_tokens

    token_score = (
        len(left_tokens & right_tokens) / len(union)
        if union
        else 0.0
    )

    return max(sequence_score, token_score)


def semantic_slug(question: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", normalize(question)).strip("_")
    return slug[:80] or "unknown_followup"


def normalize_generated_query(query: str | None) -> str:
    if query is None:
        return ""

    normalized = str(query).strip()
    normalized = normalized.replace("```prolog", "").replace("```", "").strip()

    if normalized.startswith("?-"):
        normalized = normalized[2:].strip()

    return normalized.rstrip(".").strip()


# ================================================================
# Generate test_modalities.json with Structured Outputs
# ================================================================
def extract_kb_questions(prolog_code: str) -> list[str]:
    """
    Extract literal question strings from ask_* calls
    in the generated Prolog knowledge base.
    """

    pattern = re.compile(
        r"ask_(?:boolean|numeric|string|category|range|duration|"
        r"multiple_category|multi_structured_input|multi_attribute_entity)"
        r"\s*\(\s*'((?:[^']|'')*)'",
        re.IGNORECASE,
    )

    questions = [
        match.replace("''", "'")
        for match in pattern.findall(prolog_code)
    ]

    if not questions:
        raise RuntimeError(
            "No literal ask_* question strings were found "
            "in the generated KB."
        )

    return questions
    
def generate_testcases(
    source_file: str,
    prolog_code: str,
    output_path: Path = TEST_PATH,
) -> list[dict]:
    source_path = BASE_DIR / source_file

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    medical_text = load_text(source_path)

    response = client.responses.create(
        model=TEST_GENERATOR_MODEL,
        instructions=(
            TEST_GENERATOR_INSTRUCTIONS
            + """
Return only one valid JSON object.

Do not use Markdown.
Do not use triple backticks.
Do not include explanations before or after the JSON.
Derive the key deterministically from the corresponding ask_* question.
The key must be a lowercase snake_case identifier containing only lowercase letters, digits, and underscores.

The top-level JSON structure must be:

{
  "canonical_question": "one broad diagnosis question",
  "tests": [
    {
      "id": "lowercase_snake_case",
      "question": "the canonical broad diagnosis question",
      "source_file": "source path",
      "expected_followups": [
        {
          "key": "lowercase_snake_case",
          "question": "literal question grounded in the Prolog KB",
          "modality": "boolean",
          "answer": "answer encoded as a string"
        }
      ],
      "max_followups": 1,
      "correct_answer": "expected final answer"
    }
  ]
}

Use one broad canonical end-to-end question for every test.
Do not generate unrelated questions unless they occur in the supplied source text and Prolog KB.

Every expected follow-up question must be grounded in an ask_* call
that actually exists in the supplied Prolog knowledge base.
"""
        ),
        input=(
            f"source_file:\n{source_file}\n\n"
            f"Source text:\n{medical_text}\n\n"
            f"Generated Prolog knowledge base:\n{prolog_code}"
        ),
    )

    raw_output = response.output_text.strip()

    if not raw_output:
        raise RuntimeError(
            "OpenAI returned an empty evaluation suite."
        )

    raw_output = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw_output,
        flags=re.IGNORECASE,
    ).strip()

    try:
        raw_suite = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OpenAI did not return valid JSON.\n"
            f"JSON error: {exc}\n"
            f"Raw output:\n{raw_output}"
        ) from exc

    try:
        suite = EvaluationSuite.model_validate(raw_suite)
    except Exception as exc:
        raise RuntimeError(
            "Generated JSON does not match EvaluationSuite.\n"
            f"Validation error: {exc}\n"
            f"Generated JSON:\n"
            f"{json.dumps(raw_suite, ensure_ascii=False, indent=2)}"
        ) from exc

    canonical_question = suite.canonical_question.strip()

    if not canonical_question:
        raise RuntimeError(
            "Test generation returned an empty canonical question."
        )

    kb_questions = extract_kb_questions(prolog_code)

    test_cases: list[dict] = []
    invalid_followups: list[str] = []

    for test in suite.tests:
        data = test.model_dump()

        data["source_file"] = source_file
        data["question"] = canonical_question

        for followup in data.get("expected_followups", []):
            expected_question = followup.get("question", "")

            best_score = max(
                (
                    question_similarity(
                        expected_question,
                        kb_question,
                    )
                    for kb_question in kb_questions
                ),
                default=0.0,
            )

            if best_score < 0.72:
                invalid_followups.append(
                    f"{data['id']}: "
                    f"{expected_question!r} "
                    f"(best KB match={best_score:.2f})"
                )

        test_cases.append(data)

    if invalid_followups:
        details = "\n".join(
            f"- {item}" for item in invalid_followups
        )

        raise RuntimeError(
            "Generated tests contain follow-up questions that are "
            "not grounded in the generated Prolog KB:\n"
            f"{details}\n"
            "The invalid test file was not saved."
        )

    save_json(output_path, test_cases)

    print("\n==========================")
    print("Structured test generation")
    print("==========================")
    print(f"Generated tests: {len(test_cases)}")
    print(f"Canonical question: {canonical_question}")
    print(f"Source: {source_file}")
    print(f"Saved to: {output_path}")

    return test_cases

# ================================================================
# Runtime adapter
# ================================================================


class EvalSession:
    """
    Connect expected JSON answers with the question-text cache.

    Runtime identity: exact question string used by interaction.remember().
    Evaluation identity: the semantic key stored in test_modalities.json.
    """

    def __init__(self, expected_followups: list[dict]):
        self.expected_followups = expected_followups
        self.actual_followups: list[dict] = []
        self.used_expected_keys: set[str] = set()

    def _question_score(self, actual: str, expected: str) -> float:
        a = normalize_question(actual)
        e = normalize_question(expected)

        if a == e:
            return 1.0
        if not a or not e:
            return 0.0

        a_tokens = set(a.split())
        e_tokens = set(e.split())
        token_score = len(a_tokens & e_tokens) / max(1, len(a_tokens | e_tokens))
        sequence_score = SequenceMatcher(None, a, e).ratio()
        return max(token_score, sequence_score)

    def match_expected(self, question: str, modality: str) -> dict | None:
        candidates = []

        for expected in self.expected_followups:
            key = str(expected.get("key"))
            if key in self.used_expected_keys:
                continue

            score = self._question_score(question, expected.get("question", ""))

            # Prefer the same modality, but still permit a question match so
            # a wrong predicted modality can be measured instead of hidden.
            if expected.get("modality") == modality:
                score += 0.15

            candidates.append((score, expected))

        if not candidates:
            return None

        score, expected = max(candidates, key=lambda item: item[0])
        return expected if score >= 0.45 else None

    def record_pending(self, pending) -> tuple[dict, Any]:
        question = str(pending.question)
        modality = str(pending.modality)
        options = pending.options
        expected = self.match_expected(question, modality)

        if expected is None:
            key = semantic_slug(question)
            answer = self.default_answer(modality, options)
        else:
            key = str(expected["key"])
            self.used_expected_keys.add(key)
            answer = self.convert_answer(expected.get("answer"), modality, options)

        followup = {
            "key": key,
            "question": question,
            "modality": modality,
            "options": options,
        }
        self.actual_followups.append(followup)
        return followup, answer

    @staticmethod
    def _normalized_options(options: Any) -> list[str]:
        if not isinstance(options, (list, tuple)):
            return []
        return [normalize(option) for option in options]

    def convert_answer(self, raw: Any, modality: str, options: Any) -> Any:
        if modality == "boolean":
            return normalize(raw) in {"yes", "ja", "true", "1"}

        if modality in {"numeric", "duration", "range"}:
            value = float(str(raw).replace(",", "."))
            if modality == "range" and isinstance(options, dict):
                lower = options.get("min", options.get("start"))
                upper = options.get("max", options.get("stop"))
                if lower is not None and value < float(lower):
                    raise ValueError(f"Range answer {value} is below {lower}.")
                if upper is not None and value > float(upper):
                    raise ValueError(f"Range answer {value} is above {upper}.")
            return value

        if modality == "category":
            value = normalize(raw)
            allowed = self._normalized_options(options)
            if allowed and value not in allowed:
                raise ValueError(f"Category answer {value!r} is not in {options!r}.")
            return value

        if modality == "multiple_category":
            if isinstance(raw, list):
                values = raw

            elif isinstance(raw, str):
                try:
                    values = json.loads(raw)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "Multiple-category answer must be a JSON array string, "
                        f"but received {raw!r}."
                    ) from error

            else:
                raise ValueError(
                    "Multiple-category answer must be a list "
                    "or a JSON array string."
                )

            if not isinstance(values, list):
                raise ValueError(
                    "Multiple-category answer must decode to a list."
                )

            normalized_values = [
                normalize(value)
                for value in values
            ]

            allowed = self._normalized_options(options)

            invalid = [
                value
                for value in normalized_values
                if allowed and value not in allowed
            ]

            if invalid:
                raise ValueError(
                    f"Multiple-category answers {invalid!r} "
                    f"are not in {options!r}."
                )

            return normalized_values

        if modality in {"multi_structured_input", "multi_attribute_entity"}:
            if isinstance(raw, (list, dict)):
                parsed = raw

            elif isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"{modality} answer must be a valid JSON "
                        f"list or object string, but received {raw!r}."
                    ) from error

            else:
                raise ValueError(
                    f"{modality} answer must be a JSON list or object."
                )

            if not isinstance(parsed, (list, dict)):
                raise ValueError(
                    f"{modality} answer must decode to a list or object."
                )

            return parsed

        return str(raw)

    def default_answer(self, modality: str, options: Any) -> Any:
        if modality == "boolean":
            return False
        if modality in {"numeric", "duration"}:
            return 0.0
        if modality == "range":
            if isinstance(options, dict):
                return float(options.get("min", options.get("start", 0)))
            return 0.0
        if modality == "category":
            return options[0] if isinstance(options, list) and options else "unknown"
        if modality == "multiple_category":
            return []
        if modality == "multi_structured_input":
            if isinstance(options, dict) and options.get("mode") == "grouping":
                return {str(group): [] for group in options.get("groups", [])}
            return []
        if modality == "multi_attribute_entity":
            entity = options.get("entity", "entity") if isinstance(options, dict) else "entity"
            return {"entity": entity, "data": {}}
        return ""


# ================================================================
# End-to-end evaluation
# ================================================================


def generate_eval_kb(source_file: str) -> str:
    source_path = BASE_DIR / source_file
    medical_text = load_text(source_path)
    prolog_code = generate_prolog_kb(medical_text)

    EVAL_KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_KB_PATH.write_text(prolog_code, encoding="utf-8")
    return prolog_code


def run_reasoning(query: str):
    return janus.query_once(query.strip().rstrip("."))


def evaluate_followups(expected_followups, actual_followups):
    expected_by_key = {
        str(item["key"]): item for item in expected_followups if "key" in item
    }
    actual_by_key = {
        str(item["key"]): item for item in actual_followups if "key" in item
    }

    expected_keys = set(expected_by_key)
    actual_keys = set(actual_by_key)

    if not expected_keys:
        followup_recall = 1.0
        modality_accuracy = 1.0 if not actual_keys else 0.0
        return followup_recall, modality_accuracy

    matched_keys = expected_keys & actual_keys
    followup_recall = len(matched_keys) / len(expected_keys)

    modality_matches = sum(
        expected_by_key[key]["modality"] == actual_by_key[key]["modality"]
        for key in matched_keys
    )

    # Preserve the old evaluator's strict format: missing expected questions
    # also lower modality accuracy. Extra questions are measured separately by
    # unnecessary_followups.
    modality_accuracy = modality_matches / len(expected_keys)
    return followup_recall, modality_accuracy


def evaluate_answer(
    result: dict | None,
    correct_answer: str,
) -> bool:
    """
    Compare the expected answer with the verdict returned by Prolog.

    Supported result examples:
        {"truth": True, "Result": "diabetes"}

        {
            "truth": True,
            "Result": {
                "verdict": "diabetes",
                "evidence": {...},
            },
        }

        {"truth": True, "verdict": "diabetes"}
    """
    if not result:
        return False

    expected = normalize(str(correct_answer))

    # Most common form:
    # diagnose(Result) -> {"Result": ...}
    query_result = result.get("Result")

    if isinstance(query_result, dict):
        verdict = query_result.get("verdict")

        if verdict is not None:
            return normalize(str(verdict)) == expected

    elif query_result is not None:
        return normalize(str(query_result)) == expected

    # Also support verdict returned directly at top level.
    direct_verdict = result.get("verdict")

    if direct_verdict is not None:
        return normalize(str(direct_verdict)) == expected

    # Boolean-only queries.
    truth_value = result.get("truth")

    if expected in {"yes", "true"}:
        return truth_value is True

    if expected in {"no", "false"}:
        return truth_value is False

    return False


def validate_test_cases(test_cases: list[dict]) -> None:
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError("The test file must contain a non-empty JSON list.")

    required = {
        "id", "question", "source_file", "expected_followups", "correct_answer"
    }

    for index, case in enumerate(test_cases):
        missing = required - set(case)
        if missing:
            raise ValueError(f"Test case {index} is missing: {sorted(missing)}")

        case.setdefault("max_followups", len(case["expected_followups"]))

        for followup_index, followup in enumerate(case["expected_followups"]):
            missing_followup = {"key", "question", "modality", "answer"} - set(followup)
            if missing_followup:
                raise ValueError(
                    f"Test {case['id']!r}, follow-up {followup_index} is missing: "
                    f"{sorted(missing_followup)}"
                )


def run_case(query: str, session: EvalSession) -> tuple[dict, bool, str | None]:
    """Rerun the same query until no pending UI question remains."""

    interaction.reset_all()
    error = None

    for _ in range(MAX_REASONING_STEPS):
        try:
            result = run_reasoning(query)
            interaction.clear()
            return result or {}, True, None

        except Exception as exc:
            pending = interaction.get_question()

            if pending is None:
                error = str(exc)
                return {"truth": False}, False, error

            _, answer = session.record_pending(pending)

            # The current bridge checks this cache when the same Prolog query
            # is rerun. The cache key must be the exact question string.
            interaction.remember(str(pending.question), answer)
            interaction.clear()

    error = f"Exceeded {MAX_REASONING_STEPS} follow-up steps."
    return {"truth": False}, False, error


def evaluate(test_path: Path = TEST_PATH, prolog_code: str | None = None,):
    test_cases = load_json(test_path)
    validate_test_cases(test_cases)

    if not test_cases:
        raise ValueError("No test cases found.")

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

    if prolog_code is None:
        if not EVAL_KB_PATH.exists():
            raise FileNotFoundError(
                f"Evaluation KB not found: {EVAL_KB_PATH}\n"
                "Run the evaluator once with --generate-tests."
            )

        prolog_code = EVAL_KB_PATH.read_text(
            encoding="utf-8",
        )

        print(f"Loaded existing KB: {EVAL_KB_PATH}")

    janus.consult(str(EVAL_KB_PATH))

    totals = {
        "query_validity": 0.0,
        "followup_recall": 0.0,
        "modality_accuracy": 0.0,
        "answer_accuracy": 0.0,
        "efficiency_score": 0.0,
    }
    all_results = []

    for case in test_cases:
        print("\n==========================")
        print(f"Test: {case['id']}")
        print(f"Question: {case['question']}")

        expected_followups = case.get("expected_followups", [])
        max_followups = case.get("max_followups", len(expected_followups))
        session = EvalSession(expected_followups)

        raw_query = generate_query(case["question"], prolog_code)
        query = normalize_generated_query(raw_query)
        query_valid = bool(query) and query != "fail"

        print(f"Correct answer: {case['correct_answer']}")
        print(f"Generated query: {query}")

        execution_error = None
        if query_valid:
            result, execution_ok, execution_error = run_case(query, session)
            query_valid = query_valid and execution_ok
        else:
            result = {"truth": False}

        actual_followups = session.actual_followups
        followup_recall, modality_accuracy = evaluate_followups(
            expected_followups, actual_followups
        )

        answer_correct = (
            evaluate_answer(result, case["correct_answer"]) if query_valid else False
        )
        answer_accuracy = 1.0 if answer_correct else 0.0

        actual_count = len(actual_followups)
        unnecessary_followups = max(0, actual_count - max_followups)

        if actual_count == 0:
            efficiency_score = 1.0 if max_followups == 0 and query_valid else 0.0
        else:
            efficiency_score = min(1.0, max_followups / actual_count)

        query_validity = 1.0 if query_valid else 0.0

        totals["query_validity"] += query_validity
        totals["followup_recall"] += followup_recall
        totals["modality_accuracy"] += modality_accuracy
        totals["answer_accuracy"] += answer_accuracy
        totals["efficiency_score"] += efficiency_score

        print("\nExpected followups:")
        if expected_followups:
            for followup in expected_followups:
                print(
                    f"- {followup['key']}: {followup['question']} "
                    f"[{followup['modality']}] -> {followup['answer']}"
                )
        else:
            print("- None")

        print("\nActual followups:")
        if actual_followups:
            for followup in actual_followups:
                print(
                    f"- {followup['key']}: {followup['question']} "
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
        if execution_error:
            print(f"Execution error: {execution_error}")

        all_results.append({
            "id": case["id"],
            "question": case["question"],
            "source_file": case["source_file"],
            "correct_answer": case["correct_answer"],
            "generated_query": query,
            "query_valid": query_valid,
            "expected_followups": expected_followups,
            "actual_followups": actual_followups,
            "metrics": {
                "query_validity": query_validity,
                "followup_recall": followup_recall,
                "modality_accuracy": modality_accuracy,
                "answer_accuracy": answer_accuracy,
                "efficiency_score": efficiency_score,
                "unnecessary_followups": unnecessary_followups,
            },
            "raw_result": result,
            "error": execution_error,
        })

    interaction.reset_all()

    total = len(test_cases)
    summary = {
        "total_tests": total,
        **{name: value / total for name, value in totals.items()},
        "total_unnecessary_followups": sum(
            item["metrics"]["unnecessary_followups"] for item in all_results
        ),
    }

    save_json(RESULTS_PATH, all_results)
    save_json(SUMMARY_PATH, summary)

    print("\n==========================")
    print("Overall results")
    print("==========================")
    print(f"Query validity: {summary['query_validity']:.2f}")
    print(f"Follow-up recall: {summary['followup_recall']:.2f}")
    print(f"Modality accuracy: {summary['modality_accuracy']:.2f}")
    print(f"Answer accuracy: {summary['answer_accuracy']:.2f}")
    print(f"Efficiency score: {summary['efficiency_score']:.2f}")
    print(f"Results saved to: {RESULTS_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")

    return summary, all_results


# ================================================================
# CLI
# ================================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Optionally generate test_modalities.json, then run the end-to-end "
            "modality evaluation against the interaction-based runtime."
        )
    )
    parser.add_argument("--generate-tests", action="store_true")
    parser.add_argument("--source-file", default=DEFAULT_SOURCE_FILE)
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--test-path", default=str(TEST_PATH))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    prolog_code = None

    if args.generate_tests or args.generate_only:
        prolog_code = generate_eval_kb(args.source_file)
        generate_testcases(
            source_file=args.source_file,
            prolog_code=prolog_code,
            output_path=Path(args.test_path),
        )

    if not args.generate_only:
        evaluate(test_path=Path(args.test_path), prolog_code=prolog_code)