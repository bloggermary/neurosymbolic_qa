from llm.client import client


def generate_query(question: str) -> str:
    PROMPT = """
Convert the user question into a valid Prolog query.

IMPORTANT RULES:
- Do NOT use variables (no Result, X, etc.)
- Do NOT use parentheses
- Return ONLY a predicate name

Allowed predicates:
diagnose
diabetes
prediabetes
low_risk

Examples:

Question: Diagnose the patient
Output: diagnose

Question: Does the patient have diabetes?
Output: diabetes

Return ONLY ONE WORD.
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": PROMPT + "\n\nQuestion:\n" + question}
        ]
    )

    return response.choices[0].message.content.strip().rstrip(".")