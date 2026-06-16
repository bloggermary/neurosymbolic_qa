from modalities.validation import ModalityValidator


class NumericHandler:
    """
    Handles numeric user input during Prolog reasoning.
    """

    def handle(self, question: str) -> float:
        while True:
            answer = input(f"{question} Enter numeric value: ")

            result = ModalityValidator.parse_float(answer)

            if result is not None:
                return result

            print("Please enter a numeric value, for example 126, 6.5 or 11,1.")