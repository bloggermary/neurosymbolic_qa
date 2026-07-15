from llm.client import client
from config import MODEL_NAME


ALLOWED_MODALITIES = {
    "boolean",
    "numeric",
    "string",
    "categorical",
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
    categorical
    range
    duration
    scale

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
    - Time length with a unit.
    - Years, months, weeks, days, hours.
    Examples:
    "How long have symptoms lasted?"
    "Duration of fasting?"

    range:
    - A lower and upper numeric boundary.
    - User enters a value between two numbers.
    Examples:
    "Choose a value from 1 to 10"
    "Enter glucose range"

    scale:
    - Rating questions.
    - Usually 1-10 or mild-to-severe scores.
    Examples:
    "Rate pain from 1 to 10"
    "Severity score"

    categorical:
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