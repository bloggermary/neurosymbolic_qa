from llm.client import client
from config import MODEL_NAME


ALLOWED_MODALITIES = {
    "boolean",
    "numeric",
    "multiple_choice",
    "string",
    "categorical",
}


def detect_modality(question: str) -> str:
    prompt = f"""
Classify the expected user input type for the following follow-up question.

Return exactly one of these labels:
- boolean
- numeric
- multiple_choice
- string
- categorical

Definitions:
- boolean: the user should answer yes or no.
- numeric: the user should enter a number, measurement, duration, age, score, percentage, lab value, or quantity.
- multiple_choice: the user should choose one option from an explicit list of options.
- categorical: the user should enter one category from a fixed conceptual set, such as low/medium/high, mild/moderate/severe, positive/negative, male/female/other.
- string: the user should enter free text.

Important:
- Classify only the expected input type.
- Do not classify based on the medical topic.
- Return only one label.

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