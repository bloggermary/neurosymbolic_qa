from modalities.validation import ModalityValidator


class DurationHandler:
    """
    Handles duration input, e.g. how many days a symptom has lasted.
    """

    def handle(self, question: str, unit: str = "days") -> int:
        while True:
            answer = input(f"{question} Enter duration in {unit}: ")

            result = ModalityValidator.parse_int_duration(answer)

            if result is not None:
                return result
            print("Please enter a positive whole number.")