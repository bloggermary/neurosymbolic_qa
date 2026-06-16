from modalities.validation import ModalityValidator

class BooleanHandler:
    """
    Handles boolean (Yes/No) outputs from Prolog.
    """

    def handle(self, question: str) -> bool:
        while True:
            answer = input(f"{question} [yes/no]: ")

            result = ModalityValidator.normalize_yes_no(answer)

            if result is not None:
                return result

            print("Please answer with yes/no")