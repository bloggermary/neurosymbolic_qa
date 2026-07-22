"""
Follow-up question suggestion.

Given a question and the modality already being asked, suggests at
most one complementary follow-up - a piece of clinically useful
information that ISN'T already captured by the current question's
modality (e.g. a boolean symptom question is missing duration/severity;
a bare numeric count is missing what TYPE of thing is being counted).

This is deterministic and keyword-based rather than an LLM call:
follow-up suggestion is really a lookup over a small, known set of
diabetes-related topics, and a rule table is faster, free, and
reproducible for evaluation - a free-text LLM question would almost
never match a fixed expected question string anyway.
"""

from __future__ import annotations


# keyword -> (complementary_modality, canonical_topic)
# `complementary_modality` is None when no useful follow-up applies
# (the topic is already fully specified, e.g. a lab value with units).
_TOPIC_FOLLOWUPS: dict[str, tuple[str | None, str]] = {
    "thirst": ("duration", "thirst"),
    "urinat": ("range", "urination"),
    "fatigu": ("range", "fatigue"),
    "tired": ("range", "fatigue"),
    "weight gain": ("duration", "weight_change"),
    "vision": ("string", "vision_problem"),
    "dizz": ("duration", "dizziness"),
    "hunger": ("duration", "hunger"),
    "concentrat": ("range", "concentration"),
    "headache": ("range", "headache"),
    "sleep": ("range", "sleep_quality"),
    "skin": ("string", "skin_change"),
    "pain": ("duration", "pain"),
    "weak": ("duration", "weakness"),
    "exercise": ("category", "exercise_type"),
    "physically active": ("numeric", "exercise_days"),
    "diet": ("category", "diet_type"),
    "symptom": ("string", "symptom_description"),
}

# Topics that are already self-contained and rarely need a follow-up.
_NO_FOLLOWUP_KEYWORDS = (
    "nausea",
    "glucose",
    "blood pressure",
    "how old",
    "age",
    "cups of water",
    "blurred vision",
)

# Topics whose useful complement depends on what's ALREADY being asked,
# not just the keyword (e.g. "do you have weight loss" is missing the
# AMOUNT; "how much weight did you lose" is missing the DURATION).
_CONDITIONAL_FOLLOWUPS: dict[str, dict[str, tuple[str, str]]] = {
    "weight loss": {
        "boolean": ("numeric", "weight_loss_amount"),
        "numeric": ("duration", "weight_loss_duration"),
    },
    "medication": {
        # A single medication CATEGORY pick is missing WHICH ones
        # specifically apply - a multi-select is the natural complement.
        "category": ("multiple_category", "medication_list"),
        # A plain yes/no "are you on medication" is missing WHAT the
        # medication actually is - name/dose/frequency, one entry per
        # attribute, is the natural complement.
        # Other medication phrasings (e.g. "how many medications do you
        # take?", numeric) fall through with no follow-up, unchanged.
        "boolean": ("multi_attribute_entity", "medication_details"),
    },
    "symptom": {
        # Having just picked SEVERAL symptoms at once is missing the
        # ORDER they appeared in - a natural complement once more than
        # one symptom is on the table. A single-modality "symptom"
        # question (boolean/string/etc.) falls through to the generic
        # _TOPIC_FOLLOWUPS entry below instead.
        "multiple_category": ("multi_structured_input", "symptom_order"),
    },
}


def _find_topic(
    question: str,
    modality: str | None,
) -> tuple[str | None, str | None]:
    """
    Returns (complementary_modality, canonical_topic) for the first
    matching keyword, or (None, None) if nothing matches.
    """

    lowered = question.lower()

    for keyword in _NO_FOLLOWUP_KEYWORDS:
        if keyword in lowered:
            return None, None

    for keyword, by_modality in _CONDITIONAL_FOLLOWUPS.items():
        if keyword in lowered and modality in by_modality:
            return by_modality[modality]

    for keyword, (followup_modality, topic) in _TOPIC_FOLLOWUPS.items():
        if keyword in lowered:
            return followup_modality, topic

    return None, None


def generate_followup(question: str, modality: str | None = None) -> list[dict]:
    """
    Suggest at most one follow-up question.

    Parameters
    ----------
    question:
        The original question being asked.
    modality:
        The modality already used to answer `question` (if known).
        Used to avoid suggesting a follow-up that asks for the same
        kind of information again.

    Returns
    -------
    A list containing zero or one
    {"question": str, "modality": str, "topic": str} dicts - a list
    (not a single dict) so callers can uniformly treat "no follow-up
    needed" as an empty list. `topic` is a human-readable label (for
    UI display); `question` is a stable slug (for evaluation matching).
    """

    complementary_modality, topic = _find_topic(question, modality)

    if complementary_modality is None:
        return []

    if complementary_modality == modality:
        return []

    return [
        {
            "question": f"{topic}_{complementary_modality}",
            "modality": complementary_modality,
            "topic": topic.replace("_", " "),
        }
    ]
