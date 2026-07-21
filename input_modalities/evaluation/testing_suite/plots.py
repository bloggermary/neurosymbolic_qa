import json
import os
import matplotlib.pyplot as plt

from evaluation.testing_suite.metrics import (
    aggregate_modality_distribution,
    modality_confusion_matrix,
)


BASE_PATH = "evaluation/results"
PLOT_PATH = "evaluation/results/plots"


os.makedirs(
    PLOT_PATH,
    exist_ok=True
)


# =========================================================
# Helpers
# =========================================================

def load(filename):

    path = os.path.join(
        BASE_PATH,
        filename
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_plot(name):

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_PATH,
            name
        )
    )

    plt.close()


def _bar_with_labels(labels, values, title, ylabel="", ylim=None):

    plt.figure()

    bars = plt.bar(labels, values)

    if ylim:
        plt.ylim(*ylim)

    plt.title(title)

    if ylabel:
        plt.ylabel(ylabel)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.0%}" if ylim == (0, 1) else str(value),
            ha="center",
            va="bottom",
        )


# =========================================================
# 1. MODALITY DETECTION
# =========================================================

def plot_modality_accuracy():

    data = load("modality_accuracy.json")

    _bar_with_labels(
        ["Accuracy"],
        [data["accuracy"]],
        "Modality Detection Accuracy",
        ylim=(0, 1),
    )

    save_plot("modality_accuracy.png")


def plot_modality_distribution():

    results = load("modality_results.json")

    distribution = aggregate_modality_distribution(results)

    plt.figure()

    plt.bar(distribution.keys(), distribution.values())

    plt.xticks(rotation=45)

    plt.title("Predicted Modality Distribution")

    save_plot("modality_distribution.png")


def plot_modality_confusion():

    results = load("modality_results.json")

    matrix = modality_confusion_matrix(results)

    labels = sorted(
        set(matrix.keys())
        | {p for row in matrix.values() for p in row.keys()}
    )

    grid = [
        [matrix.get(expected, {}).get(predicted, 0) for predicted in labels]
        for expected in labels
    ]

    plt.figure()

    plt.imshow(grid)

    plt.xticks(range(len(labels)), labels, rotation=45)
    plt.yticks(range(len(labels)), labels)

    plt.xlabel("Predicted")
    plt.ylabel("Expected")

    for i in range(len(labels)):
        for j in range(len(labels)):
            if grid[i][j]:
                plt.text(j, i, grid[i][j], ha="center", va="center")

    plt.title("Modality Confusion Matrix")

    save_plot("modality_confusion_matrix.png")


# =========================================================
# 2. QUERY GENERATION
# =========================================================

def plot_query_accuracy():

    data = load("query_accuracy.json")

    _bar_with_labels(
        ["Strict\n(exact predicate match)", "Keyword overlap\n(>=70%)"],
        [data["strict_accuracy"], data["keyword_accuracy"]],
        "Query Generation Accuracy",
        ylim=(0, 1),
    )

    save_plot("query_accuracy.png")


def plot_query_recall():

    data = load("query_results.json")

    scores = [x.get("keyword_overlap_score", 0) for x in data]

    plt.figure()

    plt.hist(scores, bins=10, range=(0, 1))

    plt.title("Query Keyword-Overlap Score Distribution")

    plt.xlabel("Fraction of expected predicate keywords found")
    plt.ylabel("Number of questions")

    save_plot("predicate_recall.png")


def plot_query_complexity():

    data = load("query_results.json")

    complexity = [
        query.count(",") + 1 if (query := q.get("query", "")) else 0
        for q in data
    ]

    plt.figure()

    plt.hist(complexity, bins=range(1, max(complexity, default=1) + 2))

    plt.title("Query Complexity")

    plt.xlabel("Number of goals in the generated query")
    plt.ylabel("Number of questions")

    save_plot("query_complexity.png")


# =========================================================
# 3. PIPELINE
# =========================================================

def plot_pipeline_success():

    data = load("pipeline_success.json")

    answered = data.get("answered_directly", data.get("successful", 0))
    needs_input = data.get("needs_input", 0)
    failed = data.get("failed", 0)

    _bar_with_labels(
        ["Answered\ndirectly", "Correctly asked\nfor more input", "Failed"],
        [answered, needs_input, failed],
        "Pipeline Outcomes",
        ylabel="Number of questions",
    )

    save_plot("pipeline_success.png")


def plot_pipeline_runtime():

    data = load("pipeline_results.json")

    times = [x["time"] for x in data if "time" in x]

    if not times:
        return

    plt.figure()

    plt.hist(times, bins=10)

    plt.title("Pipeline Runtime Distribution")

    plt.xlabel("Seconds")
    plt.ylabel("Number of questions")

    save_plot("pipeline_runtime.png")


def plot_pipeline_errors():

    data = load("pipeline_results.json")

    needs_input = sum(1 for x in data if x.get("needs_input"))

    other_errors = sum(
        1 for x in data
        if not x.get("success", True) and not x.get("needs_input")
    )

    if needs_input == 0 and other_errors == 0:
        return

    _bar_with_labels(
        ["Correctly needs\nmore input", "Genuine\nerror"],
        [needs_input, other_errors],
        "Pipeline Error Categories",
        ylabel="Number of questions",
    )

    save_plot("pipeline_errors.png")


# =========================================================
# 4. KB GENERATION
# =========================================================

def plot_kb_generation():

    if not os.path.exists(os.path.join(BASE_PATH, "kb_results.json")):
        return

    data = load("kb_results.json")

    success = sum(1 for x in data if x.get("success"))
    fail = len(data) - success

    plt.figure()

    plt.bar(["Success", "Failure"], [success, fail])

    plt.title(f"KB Generation ({len(data)} medical texts)")

    plt.ylabel("Number of texts")

    save_plot("kb_generation.png")

    # Per-snippet breakdown, since each text is a meaningfully different domain.
    plt.figure()

    names = [x["snippet"] for x in data]
    outcomes = [1 if x.get("success") else 0 for x in data]

    plt.bar(names, outcomes)

    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 1.2)
    plt.yticks([0, 1], ["Fail", "Pass"])

    plt.title("KB Generation by Medical Text")

    save_plot("kb_generation_by_snippet.png")


# =========================================================
# 5. FOLLOW-UP
# =========================================================

def plot_followup_accuracy():

    data = load("followup_accuracy.json")

    _bar_with_labels(
        ["Strict\n(exact wording)", "Decision\n(needed? + modality)"],
        [data["strict_accuracy"], data["decision_accuracy"]],
        "Follow-up Accuracy",
        ylim=(0, 1),
    )

    save_plot("followup_accuracy.png")


def plot_followup_count():

    data = load("followup_results.json")

    counts = [len(x.get("followups", [])) for x in data]

    plt.figure()

    plt.hist(counts, bins=[-0.5, 0.5, 1.5, 2.5])

    plt.xticks([0, 1, 2])

    plt.title("Follow-up Count Distribution")

    plt.xlabel("Follow-ups suggested per question")
    plt.ylabel("Number of questions")

    save_plot("followup_count.png")


# =========================================================
# 6. OVERVIEW
# =========================================================

def plot_overview():
    """
    One chart summarizing every eval's headline accuracy, for a
    quick at-a-glance comparison across all four test suites.
    """

    bars = []

    try:
        bars.append(("Modality\ndetection", load("modality_accuracy.json")["accuracy"]))
    except FileNotFoundError:
        pass

    try:
        bars.append(("Query gen\n(strict)", load("query_accuracy.json")["strict_accuracy"]))
        bars.append(("Query gen\n(keyword)", load("query_accuracy.json")["keyword_accuracy"]))
    except FileNotFoundError:
        pass

    try:
        bars.append(("Pipeline\nsuccess", load("pipeline_success.json")["success_rate"]))
    except FileNotFoundError:
        pass

    try:
        bars.append(("Follow-up\n(decision)", load("followup_accuracy.json")["decision_accuracy"]))
    except FileNotFoundError:
        pass

    try:
        bars.append(("KB\ngeneration", load("kb_accuracy.json")["accuracy"]))
    except FileNotFoundError:
        pass

    if not bars:
        return

    labels, values = zip(*bars)

    _bar_with_labels(
        list(labels),
        list(values),
        "Evaluation Overview",
        ylim=(0, 1),
    )

    save_plot("overview.png")


# =========================================================
# MAIN ORDER
# =========================================================

if __name__ == "__main__":


    print("Generating plots...")


    # 1 Modality
    plot_modality_accuracy()
    plot_modality_distribution()
    plot_modality_confusion()


    # 2 Query
    plot_query_accuracy()
    plot_query_recall()
    plot_query_complexity()


    # 3 Pipeline
    plot_pipeline_success()
    plot_pipeline_runtime()
    plot_pipeline_errors()


    # 4 KB
    plot_kb_generation()


    # 5 Follow-up
    plot_followup_accuracy()
    plot_followup_count()


    # 6 Overview
    plot_overview()


    print(
        "All plots saved in evaluation/results/plots/"
    )
