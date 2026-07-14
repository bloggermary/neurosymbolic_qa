from llm.client import client


# Later version must not limit the query to predefined set of allowed predicates.
def generate_query(question: str,prolog_code: str) -> str:
    PROMPT = f"""
You are a Prolog query generator.
Your task:
Convert the user question into exactly one valid SWI-Prolog query.

IMPORTANT RULES:
- Use ONLY predicates that exist in the provided Prolog knowledge base
- Return only the Prolog query
- Do not use ?-.
- If no matching predicate exists, return fail
- If the user asks a general diabetes diagnosis question, always use assess_diabetes(Result).


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