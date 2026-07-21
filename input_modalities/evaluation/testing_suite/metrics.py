import json
import os
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
# 3. Pipeline Metrics
# =========================================================

def pipeline_success_rate(results):

    success = sum(
        1
        for r in results
        if r.get("success", False)
    )


    return compute_accuracy(
        success,
        len(results)
    )



def pipeline_execution_times(results):

    return [
        r.get(
            "time",
            0
        )
        for r in results
    ]



def pipeline_error_distribution(results):

    errors = Counter()

    for r in results:

        if not r.get(
            "success",
            False
        ):

            error = r.get(
                "error",
                "unknown"
            )

            errors[error] += 1


    return dict(errors)



# =========================================================
# 4. KB Generation Metrics
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
# 5. Follow-up Metrics
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