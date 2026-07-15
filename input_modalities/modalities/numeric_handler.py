from modalities.validation import ModalityValidator


class NumericHandler:
    """
    Creates a numeric input request.

    The actual input is collected by Streamlit,
    not the terminal.
    """

    def handle(self, question: str):

        return {
            "type": "numeric",
            "question": question
        }