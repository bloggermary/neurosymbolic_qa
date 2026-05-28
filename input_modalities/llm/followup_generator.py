from client import client
from config import MODEL_NAME
from modality_detector import detect_modality

def generate_followup(missing_fact: str) -> dict:
    """
    Generates a follow-up question when Prolog lacks required information.
    Returns structured dict:
    {
        "question": str,
        "modality": str
    }
    """

    prompt = f"""
You are a medical reasoning assistant.

A Prolog system is missing information needed to continue reasoning.

Generate a clear follow-up question for the user.

Missing information:
{missing_fact}

Return format:
Question: <question>
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.choices[0].message.content.strip()

    # extract question (simple parsing for MVP)
    question = text.replace("Question:", "").strip()

    # detect modality using separate model step
    modality = detect_modality(question)

    return {
        "question": question,
        "modality": modality
    }