from llm.client import client
from config import MODEL_NAME


ALLOWED_MODALITIES = {
    "boolean",
    "numeric",
    "string",
    "category",
    "range",
    "duration"
}


def detect_modality(question: str) -> str:
    prompt = f"""
    Classify the expected user input type.

    Return ONLY ONE label:

    boolean
    numeric
    string
    category
    range
    duration

    Rules:

    boolean:
    - Yes/no answers.
    - True/false questions.

    numeric:
    - A single number value.
    - Measurements, lab values, age, weight, glucose, percentage.
    Examples:
    "Enter glucose level"
    "How old is the patient?"

    duration:
    - Time length with a unit, asked as an open-ended amount (not
      bounded by two endpoints).
    - Years, months, weeks, days, hours.
    - "When did X begin/start/first appear?" also counts as duration,
      not string - the natural answer is elapsed time ("3 weeks ago"),
      not a free-text description or calendar date.
    Examples:
    "How long have symptoms lasted?"
    "Duration of fasting?"
    "When did your symptoms begin?"
    "When did the fatigue start?"

    range:
    - A lower and upper numeric boundary is given, and the user picks
      or reports a value inside that boundary.
    - Includes rating/severity scores (e.g. 1-10, mild-to-severe),
      since those are also bounded-interval answers.
    Examples:
    "Choose a value from 1 to 10"
    "Enter glucose range"
    "Rate pain from 1 to 10"
    "Severity score from 1 to 10"

    category:
    - Choose one option from predefined categories.
    Examples:
    "Low/medium/high"
    "Male/female"
    "Type 1/type 2"

    string:
    - Free text explanation.
    Examples:
    "Describe symptoms"

    Important:
    - Ignore medical meaning.
    - Only classify the answer format.
    - Return only the label.

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )

    modality = response.choices[0].message.content.strip().lower()

    if modality not in ALLOWED_MODALITIES:
        return "string"

    return modality