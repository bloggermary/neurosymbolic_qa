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
        # The KB calls this as py_call(prolog_bridge:ask_boolean(Question), true),
        # unifying the return value against the literal Prolog atom `true`.
        # Only the Python STRING 'true' unifies with that atom - a Python bool
        # True/False does not (janus converts it to something else entirely),
        # so returning the raw cached bool here would make ask_boolean fail
        # unconditionally regardless of the real answer, once it's re-asked
        # during resume().
        return "true" if cached else "false"

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



def ask_multiple_category(question: str, categories):
    """
    Select any number of applicable options at once (e.g. "which of
    these symptoms apply?"), instead of asking one boolean per option.
    Returns a Prolog list of the selected category atoms/strings.
    """

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    interaction.request(
        question=question,
        modality="multiple_category",
        options=categories
    )

    raise WaitingForUserInput(
        question=question,
        modality="multiple_category",
        options=categories
    )



def ask_multi_structured_input(question: str, mode: str, groups=None):
    """
    Collect ordered (mode="sequence"), ranked (mode="ranking"), or
    grouped (mode="grouping", using `groups` as the group labels)
    multi-item input. Returns a Prolog list (sequence/ranking) or a
    top-level dict keyed by group name (grouping).
    """

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    options = {"mode": mode, "groups": groups or []}

    interaction.request(
        question=question,
        modality="multi_structured_input",
        options=options
    )

    raise WaitingForUserInput(
        question=question,
        modality="multi_structured_input",
        options=options
    )



def ask_multi_attribute_entity(question: str, entity: str, fields):
    """
    Collect one structured record with several typed fields in a
    single turn (e.g. a medication's name/dose/frequency), instead of
    three separate questions. `fields` is a Prolog list of
    [key, prompt, type] lists, where type is one of:
    string, int, float, bool, category. Returns a top-level dict
    {"entity": entity, "data": {key: value, ...}}.
    """

    cached = interaction.get_cached_answer(question)
    if cached is not NO_ANSWER:
        return cached

    options = {"entity": entity, "fields": fields}

    interaction.request(
        question=question,
        modality="multi_attribute_entity",
        options=options
    )

    raise WaitingForUserInput(
        question=question,
        modality="multi_attribute_entity",
        options=options
    )