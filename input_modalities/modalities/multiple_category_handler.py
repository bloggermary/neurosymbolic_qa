class MultipleCategoryHandler:
    """
    Creates a multiple-choice selection request
    (e.g. for medication, medical history, symptoms).
    """

    def handle(
        self,
        question: str,
        categories: list[str]
    ):

        return {
            "type": "multiple_category",
            "question": question,
            "options": categories
        }
