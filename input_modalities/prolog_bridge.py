"""
Python callbacks exposed to Prolog through Janus.

Prolog calls these functions when it needs
additional user information.

Streamlit handles the actual user interaction.
"""


class WaitingForUserInput(Exception):
    """
    Signal that Prolog needs information from the UI.
    """

    def __init__(
        self,
        question: str,
        modality: str,
        options=None
    ):

        self.question = question
        self.modality = modality
        self.options = options

        super().__init__(question)



def ask_numeric(question: str):

    raise WaitingForUserInput(
        question=question,
        modality="numeric"
    )



def ask_boolean(question: str):

    raise WaitingForUserInput(
        question=question,
        modality="boolean",
        options=[
            "yes",
            "no"
        ]
    )



def ask_string(question: str):

    raise WaitingForUserInput(
        question=question,
        modality="string"
    )



def ask_category(
    question: str,
    categories
):

    raise WaitingForUserInput(
        question=question,
        modality="category",
        options=categories
    )



def ask_range(
    question: str,
    start: int,
    stop: int
):

    raise WaitingForUserInput(
        question=question,
        modality="range",
        options={
            "min": start,
            "max": stop
        }
    )



def ask_duration(question: str):

    raise WaitingForUserInput(
        question=question,
        modality="duration"
    )