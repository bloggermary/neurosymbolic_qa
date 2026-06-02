from llm.client import client


# Later version must not limit the query to predefined set of allowed predicates.
def generate_query(question: str,prolog_code: str) -> str:
    PROMPT = """
Convert the user question into a valid Prolog query.

IMPORTANT RULES:
- Use ONLY predicates that exist in the provided Prolog knowledge base
- Do NOT use variables (no Result, X, etc.)
- Do NOT use parentheses
- Return ONLY a predicate name
- Return only the Prolog query
- Do not use ?-.
- If no matching predicate exists, return fail

Examples:

Question: Diagnose the patient
Output: diagnose

Question: Does the patient have diabetes?
Output: diabetes

    Available Prolog knowledge base:
    {prolog_code}

    User question:
    {question}

"""


    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": PROMPT + "\n\nQuestion:\n" + question}],
    )

    return response.choices[0].message.content.strip().rstrip(".")
