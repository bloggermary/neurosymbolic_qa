class CategoryHandler:
    """
    Creates a category selection request.
    """

    def handle(
        self,
        question: str,
        permissible_categories: list[str]
    ):

        return {
            "type": "category",
            "question": question,
            "options": permissible_categories
        }