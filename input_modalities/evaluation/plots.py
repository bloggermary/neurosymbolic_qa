import json
import os
import matplotlib.pyplot as plt


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



# =========================================================
# 1. MODALITY DETECTION
# =========================================================

def plot_modality_accuracy():

    data = load(
        "modality_metrics.json"
    )

    accuracy = data["accuracy"]


    plt.figure()

    plt.bar(
        ["Accuracy"],
        [accuracy]
    )

    plt.ylim(
        0,
        1
    )

    plt.title(
        "Modality Detection Accuracy"
    )

    save_plot(
        "modality_accuracy.png"
    )



def plot_modality_distribution():

    data = load(
        "modality_distribution.json"
    )


    plt.figure()

    plt.bar(
        data.keys(),
        data.values()
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Predicted Modality Distribution"
    )

    save_plot(
        "modality_distribution.png"
    )



def plot_modality_confusion():

    data = load(
        "modality_confusion_matrix.json"
    )


    labels = list(data.keys())


    matrix = []

    for expected in labels:

        row=[]

        for predicted in labels:

            row.append(
                data.get(expected, {})
                    .get(predicted,0)
            )

        matrix.append(row)


    plt.figure()

    plt.imshow(
        matrix
    )

    plt.xticks(
        range(len(labels)),
        labels,
        rotation=45
    )

    plt.yticks(
        range(len(labels)),
        labels
    )

    plt.xlabel(
        "Predicted"
    )

    plt.ylabel(
        "Expected"
    )

    plt.title(
        "Modality Confusion Matrix"
    )

    save_plot(
        "modality_confusion_matrix.png"
    )



# =========================================================
# 2. QUERY GENERATION
# =========================================================

def plot_query_accuracy():

    data = load(
        "query_metrics.json"
    )


    plt.figure()

    plt.bar(
        ["Accuracy"],
        [data["accuracy"]]
    )

    plt.ylim(
        0,
        1
    )

    plt.title(
        "Query Generation Accuracy"
    )

    save_plot(
        "query_accuracy.png"
    )



def plot_query_recall():

    data = load(
        "results/query_results.json"
    )


    recalls = [
        x.get(
            "predicate_recall",
            0
        )
        for x in data
    ]


    plt.figure()

    plt.hist(
        recalls,
        bins=10
    )

    plt.title(
        "Predicate Recall Distribution"
    )

    plt.xlabel(
        "Recall"
    )

    plt.ylabel(
        "Frequency"
    )

    save_plot(
        "predicate_recall.png"
    )



def plot_query_complexity():

    data = load(
        "results/query_results.json"
    )


    complexity=[]


    for q in data:

        query=q.get(
            "query",
            ""
        )

        complexity.append(
            query.count(",")+1
            if query
            else 0
        )


    plt.figure()

    plt.hist(
        complexity,
        bins=5
    )

    plt.title(
        "Query Complexity"
    )

    plt.xlabel(
        "Number of predicates"
    )

    save_plot(
        "query_complexity.png"
    )



# =========================================================
# 3. PIPELINE
# =========================================================

def plot_pipeline_success():

    data = load(
        "pipeline_metrics.json"
    )


    plt.figure()

    plt.bar(
        ["Success"],
        [data["success_rate"]]
    )

    plt.ylim(
        0,
        1
    )

    plt.title(
        "Pipeline Success Rate"
    )

    save_plot(
        "pipeline_success.png"
    )



def plot_pipeline_runtime():

    data = load(
        "results/pipeline_results.json"
    )


    times=[]


    for x in data:

        if "time" in x:

            times.append(
                x["time"]
            )


    plt.figure()

    plt.hist(
        times,
        bins=10
    )

    plt.title(
        "Pipeline Runtime Distribution"
    )

    plt.xlabel(
        "Seconds"
    )

    save_plot(
        "pipeline_runtime.png"
    )



def plot_pipeline_errors():

    data = load(
        "results/pipeline_results.json"
    )


    errors={}


    for x in data:

        if "error" in x:

            err=x["error"]

            errors[err]=(
                errors.get(err,0)+1
            )


    if not errors:
        return


    plt.figure()

    plt.bar(
        errors.keys(),
        errors.values()
    )

    plt.xticks(
        rotation=90
    )

    plt.title(
        "Pipeline Error Types"
    )

    save_plot(
        "pipeline_errors.png"
    )



# =========================================================
# 4. KB GENERATION
# =========================================================

def plot_kb_generation():

    data = load(
        "kb_results.json"
    )


    success=sum(
        1
        for x in data
        if x.get("success")
    )


    fail=len(data)-success


    plt.figure()

    plt.bar(
        ["Success","Failure"],
        [success,fail]
    )


    plt.title(
        "KB Generation"
    )

    save_plot(
        "kb_generation.png"
    )



# =========================================================
# 5. FOLLOW-UP
# =========================================================

def plot_followup_accuracy():

    data = load(
        "followup_metrics.json"
    )


    plt.figure()

    plt.bar(
        ["Accuracy"],
        [data["accuracy"]]
    )

    plt.ylim(
        0,
        1
    )

    plt.title(
        "Follow-up Accuracy"
    )

    save_plot(
        "followup_accuracy.png"
    )



def plot_followup_count():

    data = load(
        "followup_results.json"
    )


    counts=[
        len(
            x.get(
                "predicted",
                []
            )
        )
        for x in data
    ]


    plt.figure()

    plt.hist(
        counts,
        bins=5
    )


    plt.title(
        "Follow-up Count Distribution"
    )


    save_plot(
        "followup_count.png"
    )



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


    print(
        "All plots saved in evaluation/results/plots/"
    )