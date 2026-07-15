class BooleanHandler:
    """
    Creates a yes/no input request
    for the Streamlit interface.
    """

    def handle(self, question: str):

        return {
            "type": "boolean",
            "question": question,
            "options": [
                "yes",
                "no"
            ]
        }