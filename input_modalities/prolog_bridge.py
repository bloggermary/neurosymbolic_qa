"""
Python callbacks exposed to Prolog through Janus.

Prolog calls these functions when it needs
additional user information.

Streamlit handles the actual user interaction.

A Prolog query can't be paused mid-execution and resumed later -
once py_call raises, the query has failed. So instead, every ask_*
function first checks services.interaction.answers for a cached
answer to this exact question. If present, it returns immediately
(no interruption). Only the first not-yet-answered question raises
WaitingForUserInput. Once the user answers, the pipeline re-runs
the same query from scratch - the cache means previously answered
questions are skipped and reasoning simply continues past them.

Each ask_* function registers the pending question with
`interaction` itself (modality and options included) *before*
raising. This matters because once WaitingForUserInput crosses the
py_call boundary into Prolog and back out via janus.query_once, only
its string message survives - modality/options on the exception
object are lost. Registering here, in the same Python call where the
real object still exists, is what lets the UI render the right
widget (slider, radio, selectbox, ...) instead of always falling
back to a plain number input.
"""

from services.interaction_service import interaction, NO_ANSWER


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

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(question=question, modality="numeric")

    raise WaitingForUserInput(
        question=question,
        modality="numeric"
    )



def ask_boolean(question: str):

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(
        question=question,
        modality="boolean",
        options=["yes", "no"]
    )

    raise WaitingForUserInput(
        question=question,
        modality="boolean",
        options=[
            "yes",
            "no"
        ]
    )



def ask_string(question: str):

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(question=question, modality="string")

    raise WaitingForUserInput(
        question=question,
        modality="string"
    )



def ask_category(
    question: str,
    categories
):

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(
        question=question,
        modality="category",
        options=categories
    )

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

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(
        question=question,
        modality="range",
        options={"min": start, "max": stop}
    )

    raise WaitingForUserInput(
        question=question,
        modality="range",
        options={
            "min": start,
            "max": stop
        }
    )



def ask_duration(question: str):

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(question=question, modality="duration")

    raise WaitingForUserInput(
        question=question,
        modality="duration"
    )



def ask_scale(question: str):

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(
        question=question,
        modality="scale",
        options={"min": 1, "max": 10}
    )

    raise WaitingForUserInput(
        question=question,
        modality="scale",
        options={
            "min": 1,
            "max": 10
        }
    )