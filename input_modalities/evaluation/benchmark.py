
from input_modalities.evaluation.tests.test_modality_detection import run as run_modality
from input_modalities.evaluation.tests.test_query_generation import run as run_query
from input_modalities.evaluation.tests.test_pipeline import run as run_pipeline
from input_modalities.evaluation.tests.test_followups import run as run_followups
from input_modalities.evaluation.tests.test_complexity_and_metrics import run as run_metrics




def main():

    print("\n[1] Modality detection")

    run_modality()

    print("\n[2] Query generation")

    run_query()

    print("\n[3] Pipeline execution")

    run_pipeline()

    print("\n[4] Follow-up evaluation")

    run_followups()

    print("\n[5] Extended metrics")

    run_metrics()

    print("\nALL EVALUATIONS COMPLETED")




if __name__ == "__main__":
    main()