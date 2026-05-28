from llm.client import client
from config import MODEL_NAME

def detect_modality(question: str) -> str:
    """
    Classifies the expected answer type for a follow-up question.
    Output: boolean | numeric | multiple_choice | string | categorical
    """

    prompt = f"""
Classify the following medical question into one of these modalities:

- boolean (yes/no question)
- numeric (requires number input, e.g. lab values, age)
- multiple_choice (selection from options)
- string (free text answer)
- categorical (fixed medical categories like blood type)

Return ONLY one word.

Question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip().lower()