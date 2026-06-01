from llm.client import client


# FEEDBACK: The query generation must be done for a concrete Prolog knowledge base such that the LLM knows the available predicates!
# def generate_query(question: str, prolog_code: str) -> str:
# Later version must not limit the query to predefined set of allowed predicates.
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
    # Here is the available Prolog knowledge base the Prolog query must be executable on:
    # {prolog_code}

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": PROMPT + "\n\nQuestion:\n" + question}],
    )

    return response.choices[0].message.content.strip().rstrip(".")
