
from tests.test_modality_detection import run as run_modality
from tests.test_query_generation import run as run_query
from tests.test_pipeline import run as run_pipeline
from tests.test_followups import run as run_followups


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

    print("\nALL EVALUATIONS COMPLETED")




if __name__ == "__main__":
    main()