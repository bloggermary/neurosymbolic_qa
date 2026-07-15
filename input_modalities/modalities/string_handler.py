class StringHandler:
    """
    Creates a text input request
    for Streamlit.
    """

    def handle(self, question: str):

        return {
            "type": "string",
            "question": question
        }