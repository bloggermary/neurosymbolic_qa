class ScaleHandler:
    """
    Creates a scale input request.
    Used for bounded rating scales such as 1-10, 1-5, etc.
    """

    def handle(
        self,
        question: str,
        min_value: int,
        max_value: int
    ):

        return {
            "type": "scale",
            "question": question,
            "min": min_value,
            "max": max_value
        }