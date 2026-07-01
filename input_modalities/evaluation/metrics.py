import json
from collections import Counter


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_accuracy(correct, total):
    if total == 0:
        return 0.0
    return correct / total


def aggregate_modality_distribution(results):
    counter = Counter()
    for r in results:
        counter[r["predicted"]] += 1
    return dict(counter)

def predicate_recall(expected, query):
    if not expected:
        return 0

    found = sum(1 for p in expected if p in query)
    return found / len(expected)


# -----------------------------

# Query Complexity

# -----------------------------

def compute_query_complexity(query: str) -> int:

    """

    Complexity = number of predicates (rough approximation)

    """

    if not query:

        return 0

    return query.count(",") + 1

def average_complexity(results):

    if not results:

        return 0

    return sum(r["complexity"] for r in results) / len(results)

# -----------------------------

# Follow-up Count

# -----------------------------

def average_followups(results):

    if not results:

        return 0

    return sum(len(r.get("followups", [])) for r in results) / len(results)

# -----------------------------

# Error Rate

# -----------------------------

def compute_error_rate(results):

    if not results:

        return 0

    errors = sum(1 for r in results if not r.get("success", False))

    return errors / len(results)

# -----------------------------

# Intent Accuracy

# -----------------------------

def compute_intent_accuracy(results):

    correct = sum(1 for r in results if r.get("intent_correct", False))

    return compute_accuracy(correct, len(results))

# -----------------------------

# Modality Confusion Matrix

# -----------------------------

def build_confusion_matrix(results):

    matrix = defaultdict(lambda: defaultdict(int))

    for r in results:

        expected = r["expected"]

        predicted = r["predicted"]

        matrix[expected][predicted] += 1

    return matrix

def save_confusion_matrix(matrix, path):

    save_json(path, matrix)