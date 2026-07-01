import json
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np


# load helpers
def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# 1. MODALITY EVALUATION
def plot_modality_evaluation():
    data = load("evaluation/results/modality_results.json")

    correct = 0
    total = len(data)

    per_class = Counter()

    for r in data:
        expected = r["expected"]
        predicted = r["predicted"]

        if expected == predicted:
            correct += 1

        per_class[(expected, predicted)] += 1

    accuracy = correct / total if total else 0

    print(f"Modality Accuracy: {accuracy:.2f}")

    # accuracy bar
    plt.figure()
    plt.bar(["Accuracy"], [accuracy])
    plt.ylim(0, 1)
    plt.title("Modality Detection Accuracy")
    plt.show()

    # confusion-style simple heat visualization
    labels = list(set([r["expected"] for r in data] + [r["predicted"] for r in data]))

    matrix = np.zeros((len(labels), len(labels)))

    label_index = {l: i for i, l in enumerate(labels)}

    for r in data:
        i = label_index[r["expected"]]
        j = label_index[r["predicted"]]
        matrix[i][j] += 1

    plt.figure()
    plt.imshow(matrix)
    plt.xticks(range(len(labels)), labels, rotation=45)
    plt.yticks(range(len(labels)), labels)
    plt.title("Modality Confusion Matrix")
    plt.colorbar()
    plt.show()


# 2. FOLLOW-UP EVALUATION
def plot_followup_evaluation():
    data = load("evaluation/results/followup_results.json")

    tp = fp = fn = 0

    for r in data:
        expected = set(r.get("expected_followups", []))
        predicted = set(r.get("predicted_followups", []))

        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)

    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)

    print("Follow-up Evaluation")
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1:", f1)

    plt.figure()
    plt.bar(["Precision", "Recall", "F1"], [precision, recall, f1])
    plt.ylim(0, 1)
    plt.title("Follow-up Performance")
    plt.show()


# 3. QUERY GENERATION
def plot_query_generation():
    data = load("evaluation/results/query_results.json")

    correct = 0

    for r in data:
        query = r["generated_query"]
        expected_keywords = r.get("expected_query_contains", [])

        if all(k in query for k in expected_keywords):
            correct += 1

    acc = correct / len(data)

    plt.figure()
    plt.bar(["Query Accuracy"], [acc])
    plt.ylim(0, 1)
    plt.title("Query Generation Accuracy")
    plt.show()


# 4. KB GENERATION
def plot_kb_generation():
    data = load("evaluation/results/kb_results.json")

    predicate_score = []
    rule_score = []

    for r in data:
        pred_acc = r.get("predicate_accuracy", 0)
        rule_acc = r.get("rule_accuracy", 0)

        predicate_score.append(pred_acc)
        rule_score.append(rule_acc)

    plt.figure()
    plt.plot(predicate_score, label="Predicate Accuracy")
    plt.plot(rule_score, label="Rule Accuracy")
    plt.ylim(0, 1)
    plt.legend()
    plt.title("KB Generation Quality")
    plt.show()


# 5. PIPELINE SUCCESS
def plot_pipeline_success():
    data = load("evaluation/results/pipeline_results.json")

    success = sum(1 for r in data if r["success"])
    failure = len(data) - success

    plt.figure()
    plt.pie([success, failure], labels=["Success", "Failure"], autopct="%1.1f%%")
    plt.title("End-to-End Pipeline Success")
    plt.show()


# 6. COMPLEXITY ANALYSIS
def plot_complexity():
    data = load("evaluation/results/complexity_results.json")

    easy = [r["score"] for r in data if r["difficulty"] == "easy"]
    medium = [r["score"] for r in data if r["difficulty"] == "medium"]
    hard = [r["score"] for r in data if r["difficulty"] == "hard"]

    plt.figure()
    plt.bar(["Easy", "Medium", "Hard"], [
        np.mean(easy) if easy else 0,
        np.mean(medium) if medium else 0,
        np.mean(hard) if hard else 0
    ])
    plt.ylim(0, 1)
    plt.title("Performance vs Complexity")
    plt.show()


# RUN ALL
if __name__ == "__main__":
    plot_modality_evaluation()
    plot_followup_evaluation()
    plot_query_generation()
    plot_kb_generation()
    plot_pipeline_success()
    plot_complexity()