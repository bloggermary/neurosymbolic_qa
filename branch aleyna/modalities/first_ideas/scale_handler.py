from modalities.validation import ModalityValidator

class ScaleHandler:
    """
    Handles questions that require a scale input (e.g., pain level from 1 to 10).
    Handles subjective rating scales (e.g. pain, fatigue severity).
    Example: 1-10 scale.
    """

    def handle(self, question: str, scale_min: int, scale_max: int) -> int:
        while True:
            answer = input(f"{question} (rate from {scale_min} to {scale_max}): ")

            result = ModalityValidator.parse_int_range(
                answer,
                scale_min,
                scale_max 
            )

            if result is not None:
                return result
            
            print(f"Please enter an integer value between {scale_min} and {scale_max}.")
