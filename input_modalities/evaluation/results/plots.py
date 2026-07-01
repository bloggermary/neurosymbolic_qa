import json
import matplotlib.pyplot as plt


def load(path):
    with open(path) as f:
        return json.load(f)


def plot_modality_distribution():
    data = load("evaluation/results/modality_results.json")

    counts = {}
    for r in data:
        m = r["predicted"]
        counts[m] = counts.get(m, 0) + 1

    plt.bar(counts.keys(), counts.values())
    plt.title("Modality Distribution")
    plt.show()


def plot_pipeline_success():
    data = load("evaluation/results/pipeline_success.json")

    labels = ["Success", "Failure"]
    values = [data["success_rate"], 1 - data["success_rate"]]

    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Pipeline Success Rate")
    plt.show()