
from evaluation.tests.test_modality_detection import run as run_modality
from evaluation.tests.test_query_generation import run as run_query
from evaluation.tests.test_followups import run as run_followups
from evaluation.tests.test_kb_generation import run as run_kb_generation
from evaluation.tests.test_diagnostic_accuracy import run as run_diagnostic_accuracy

from evaluation.testing_suite import plots


def main():

    print("\n[1] Modality detection")

    run_modality()

    print("\n[2] Query generation")

    run_query()

    print("\n[3] Follow-up evaluation")

    run_followups()

    print("\n[4] KB generation")

    run_kb_generation()

    print("\n[5] Diagnostic accuracy")

    run_diagnostic_accuracy()

    print("\n[6] Generating plots")

    plots.plot_modality_accuracy()
    plots.plot_modality_distribution()
    plots.plot_modality_confusion()

    plots.plot_query_accuracy()
    plots.plot_query_recall()
    plots.plot_query_complexity()

    plots.plot_kb_generation()

    plots.plot_followup_accuracy()
    plots.plot_followup_count()

    plots.plot_diagnostic_accuracy()
    plots.plot_diagnostic_by_category()

    plots.plot_overview()

    print("\nALL EVALUATIONS COMPLETED")




if __name__ == "__main__":
    main()
