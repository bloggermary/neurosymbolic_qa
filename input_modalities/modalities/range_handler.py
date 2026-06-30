from modalities.validation import ModalityValidator

class RangeHandler:
    """
    Handles numeric user input that must fall within a specific range.
    """

    def handle(self, question: str, start: int, stop: int) -> int:
        while True:
            answer = input(f"{question} Enter a value between {start} and {stop}: ")

            result = ModalityValidator.parse_int_range(answer, start, stop)

            if result is not None:
                return result

            print(f"Please enter an integer value between {start} and {stop}.")