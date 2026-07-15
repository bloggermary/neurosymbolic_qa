class RangeHandler:
    """
    Creates a numeric range input request.
    """

    def handle(
        self,
        question: str,
        start: int,
        stop: int
    ):

        return {
            "type": "range",
            "question": question,
            "min": start,
            "max": stop
        }