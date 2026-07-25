"""Create presentation-ready diagrams from modalities_evaluator_mariam.py output."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
PLOT_DIR = RESULTS_DIR / "plots" / "modalities"
RESULTS_PATH = RESULTS_DIR / "modalities_evaluation_results.json"
SUMMARY_PATH = RESULTS_DIR / "modalities_evaluation_summary.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_plot(filename: str) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(PLOT_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close()


def add_bar_labels(bars, percentage: bool = False) -> None:
    for bar in bars:
        value = bar.get_height()
        label = f"{value:.0%}" if percentage else f"{value:g}"
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            label,
            ha="center",
            va="bottom",
        )


def plot_overall_metrics(summary: dict) -> None:
    labels = [
        "Query\nvalidity",
        "Follow-up\nrecall",
        "Modality\naccuracy",
        "Answer\naccuracy",
        "Efficiency\nscore",
    ]
    values = [
        summary["query_validity"],
        summary["followup_recall"],
        summary["modality_accuracy"],
        summary["answer_accuracy"],
        summary["efficiency_score"],
    ]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(labels, values, width=0.55)
    plt.ylim(0, 1.12)
    plt.ylabel("Score")
    plt.title(f"End-to-End Modality Evaluation ({summary['total_tests']} tests)")
    add_bar_labels(bars, percentage=True)
    save_plot("modalities_overview.png")


def plot_metrics_per_test(results: list[dict]) -> None:
    metric_names = [
        "followup_recall",
        "modality_accuracy",
        "answer_accuracy",
        "efficiency_score",
    ]
    labels = [item["id"] for item in results]

    plt.figure(figsize=(max(10, len(labels) * 0.9), 6))

    width = 0.18
    x_positions = list(range(len(labels)))

    for metric_index, metric in enumerate(metric_names):
        offset = (metric_index - 1.5) * width
        values = [item["metrics"][metric] for item in results]
        plt.bar(
            [x + offset for x in x_positions],
            values,
            width=width,
            label=metric.replace("_", " ").title(),
        )

    plt.xticks(x_positions, labels, rotation=45, ha="right")
    plt.ylim(0, 1.12)
    plt.ylabel("Score")
    plt.title("Evaluation Metrics by Test Case")
    plt.legend()
    save_plot("metrics_by_test.png")


def plot_expected_vs_actual_followups(results: list[dict]) -> None:
    labels = [item["id"] for item in results]
    expected = [len(item["expected_followups"]) for item in results]
    actual = [len(item["actual_followups"]) for item in results]

    x_positions = list(range(len(labels)))
    width = 0.38

    plt.figure(figsize=(max(10, len(labels) * 0.9), 6))
    plt.bar([x - width / 2 for x in x_positions], expected, width, label="Expected")
    plt.bar([x + width / 2 for x in x_positions], actual, width, label="Actual")
    plt.xticks(x_positions, labels, rotation=45, ha="right")
    plt.ylabel("Number of follow-ups")
    plt.title("Expected vs Actual Follow-up Count")
    plt.legend()
    save_plot("expected_vs_actual_followups.png")


def plot_unnecessary_followups(results: list[dict]) -> None:
    labels = [item["id"] for item in results]
    values = [item["metrics"]["unnecessary_followups"] for item in results]

    plt.figure(figsize=(max(10, len(labels) * 0.9), 5))
    bars = plt.bar(labels, values, width=0.55)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Unnecessary follow-ups")
    plt.title("Unnecessary Follow-ups by Test Case")
    add_bar_labels(bars)
    save_plot("unnecessary_followups.png")


def plot_actual_modality_distribution(results: list[dict]) -> None:
    counts = Counter(
        followup["modality"]
        for item in results
        for followup in item["actual_followups"]
    )

    labels = sorted(counts)
    values = [counts[label] for label in labels]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(labels, values, width=0.55)
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Number of questions")
    plt.title("Actual Follow-up Modality Distribution")
    add_bar_labels(bars)
    save_plot("actual_modality_distribution.png")


def plot_followup_modality_confusion(results: list[dict]) -> None:
    matrix = defaultdict(lambda: defaultdict(int))

    for item in results:
        expected_by_key = {
            str(f["key"]): f for f in item["expected_followups"] if "key" in f
        }
        actual_by_key = {
            str(f["key"]): f for f in item["actual_followups"] if "key" in f
        }

        for key in set(expected_by_key) & set(actual_by_key):
            expected = expected_by_key[key]["modality"]
            actual = actual_by_key[key]["modality"]
            matrix[expected][actual] += 1

    labels = sorted(
        set(matrix)
        | {actual for row in matrix.values() for actual in row}
    )

    if not labels:
        return

    grid = [
        [matrix[expected].get(actual, 0) for actual in labels]
        for expected in labels
    ]

    plt.figure(figsize=(8, 7))
    plt.imshow(grid)
    plt.xticks(range(len(labels)), labels, rotation=40, ha="right")
    plt.yticks(range(len(labels)), labels)
    plt.xlabel("Actual modality")
    plt.ylabel("Expected modality")
    plt.title("Follow-up Modality Confusion Matrix")

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            plt.text(column_index, row_index, str(value), ha="center", va="center")

    save_plot("followup_modality_confusion_matrix.png")


def main() -> None:
    if not RESULTS_PATH.exists() or not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "Run modalities_evaluator_mariam.py first. Expected files:\n"
            f"- {RESULTS_PATH}\n- {SUMMARY_PATH}"
        )

    results = load_json(RESULTS_PATH)
    summary = load_json(SUMMARY_PATH)

    plot_overall_metrics(summary)
    plot_metrics_per_test(results)
    plot_expected_vs_actual_followups(results)
    plot_unnecessary_followups(results)
    plot_actual_modality_distribution(results)
    plot_followup_modality_confusion(results)

    print(f"All modality evaluation plots saved in: {PLOT_DIR}")


if __name__ == "__main__":
    main()