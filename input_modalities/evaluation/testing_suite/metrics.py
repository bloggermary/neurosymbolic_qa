import json
import os
import re
from collections import Counter, defaultdict


# =========================================================
# File handling
# =========================================================

def save_json(path, data):
    """
    Saves JSON and creates missing directories automatically.
    """

    directory = os.path.dirname(path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



# =========================================================
# General Accuracy
# =========================================================

def compute_accuracy(correct, total):

    if total == 0:
        return 0.0

    return correct / total



# =========================================================
# 1. Modality Detection Metrics
# =========================================================

def compute_modality_accuracy(results):

    correct = 0

    for r in results:

        if (
            r.get("expected")
            ==
            r.get("predicted")
        ):
            correct += 1

    return compute_accuracy(
        correct,
        len(results)
    )



def aggregate_modality_distribution(results):

    counter = Counter()

    for r in results:

        predicted = r.get(
            "predicted",
            "unknown"
        )

        counter[predicted] += 1

    return dict(counter)



def modality_confusion_matrix(results):

    matrix = defaultdict(
        lambda: defaultdict(int)
    )

    for r in results:

        expected = r.get(
            "expected",
            "unknown"
        )

        predicted = r.get(
            "predicted",
            "unknown"
        )

        matrix[expected][predicted] += 1


    return {
        k: dict(v)
        for k, v in matrix.items()
    }



# =========================================================
# 2. Query Generation Metrics
# =========================================================

def predicate_recall(expected, query):

    if not expected:
        return 0


    query = query.lower()

    matched = 0

    for predicate in expected:

        if predicate.lower() in query:
            matched += 1


    return matched / len(expected)



# Connector words that don't carry predicate-identifying meaning on
# their own (e.g. "diabetes_positive_by_fasting_glucose" vs a model
# writing "diabetes_positive_fasting_glucose" - dropping "by" shouldn't
# count against it).
_STOPWORDS = {"by", "is", "of", "the", "a"}


def _tokenize(text: str) -> set:
    """
    Splits an identifier or query string into lowercase word tokens,
    e.g. "diabetes_positive_by_fasting_glucose" ->
    {"diabetes", "positive", "fasting", "glucose"} (stopwords dropped).
    """

    words = re.findall(r"[a-zA-Z]+", text.lower())

    return {w for w in words if w not in _STOPWORDS}


def keyword_predicate_overlap(expected_predicate: str, query: str) -> float:
    """
    Fraction of `expected_predicate`'s meaningful word tokens that
    appear anywhere in `query`, regardless of exact naming, word
    order, or connector words. More forgiving than predicate_recall's
    exact-substring check: "fasting_glucose_mgdl" and
    "fasting_plasma_glucose_value" would overlap heavily even though
    neither is a substring of the other.
    """

    expected_tokens = _tokenize(expected_predicate)

    if not expected_tokens:
        return 1.0

    query_tokens = _tokenize(query)

    matched = expected_tokens & query_tokens

    return len(matched) / len(expected_tokens)


def keyword_query_score(expected_predicates, query) -> float:
    """
    Average keyword overlap across all expected predicates for one
    query - a single 0-1 "how much of the intended meaning is there"
    score, rather than requiring every predicate to match exactly.
    """

    if not expected_predicates:
        return 1.0

    scores = [
        keyword_predicate_overlap(predicate, query)
        for predicate in expected_predicates
    ]

    return sum(scores) / len(scores)



def query_accuracy(results):

    correct = sum(
        1
        for r in results
        if r.get("correct", False)
    )


    return compute_accuracy(
        correct,
        len(results)
    )



def query_predicate_scores(results):

    """
    Returns individual recall values
    so graphs can plot every question.
    """

    scores = []

    for r in results:

        score = predicate_recall(
            r.get(
                "expected_predicates",
                []
            ),
            r.get(
                "query",
                ""
            )
        )

        scores.append(score)

    return scores



# =========================================================
# 3. KB Generation Metrics
# =========================================================

def kb_generation_success(results):

    success = sum(
        1
        for r in results
        if r.get(
            "success",
            False
        )
    )


    return compute_accuracy(
        success,
        len(results)
    )



# =========================================================
# 4. Follow-up Metrics
# =========================================================

def average_followups(results):

    if not results:
        return 0


    total = sum(
        len(
            r.get(
                "followups",
                []
            )
        )
        for r in results
    )


    return total / len(results)



def followup_accuracy(results):

    correct = 0
    total = 0


    for r in results:

        expected = r.get(
            "expected_followups",
            []
        )

        predicted = r.get(
            "followups",
            []
        )


        total += len(expected)


        for item in expected:

            if item in predicted:
                correct += 1


    return compute_accuracy(
        correct,
        total
    )



# =========================================================
# Error Metrics
# =========================================================

def compute_error_rate(results):

    errors = sum(
        1
        for r in results
        if not r.get(
            "success",
            False
        )
    )


    return compute_accuracy(
        errors,
        len(results)
    )



# =========================================================
# Confusion Matrix Utility
# =========================================================

def build_confusion_matrix(results):

    matrix = defaultdict(
        lambda: defaultdict(int)
    )


    for r in results:

        expected = r.get(
            "expected",
            "unknown"
        )

        predicted = r.get(
            "predicted",
            "unknown"
        )


        matrix[expected][predicted] += 1


    return {
        key: dict(value)
        for key, value in matrix.items()
    }



def save_confusion_matrix(matrix, path):

    save_json(
        path,
        matrix
    )