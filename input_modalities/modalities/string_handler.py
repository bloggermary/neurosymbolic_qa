from modalities.validation import ModalityValidator


class StringHandler:
    """
    Handles textual user input during Prolog reasoning.
    """

    def handle(self, question: str) -> str:
        while True:
            answer = input(f"{question} Enter text value: ")

            result = ModalityValidator.normalize_string(answer)

            if result:
                return result

            print("Please enter a non-empty text value.")