class MultiStructuredInputHandler:
    """
    Creates a structured multi-input request.
    Supported modes: sequence, ranking, grouping.
    """

    def handle(
        self,
        question: str,
        mode: str,
        groups: list[str] | None = None
    ):

        return {
            "type": "multi_structured_input",
            "question": question,
            "mode": mode,
            "groups": groups or []
        }
