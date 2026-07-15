class DurationHandler:
    """
    Creates a duration input request.
    """

    def handle(
        self,
        question: str,
        unit: str = "days"
    ):

        return {
            "type": "duration",
            "question": question,
            "unit": unit
        }