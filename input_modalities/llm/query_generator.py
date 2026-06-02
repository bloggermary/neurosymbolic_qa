from llm.client import client


# Later version must not limit the query to predefined set of allowed predicates.
def generate_query(question: str,prolog_code: str) -> str:
    PROMPT = """
Convert the user question into a valid Prolog query.

IMPORTANT RULES:
- Use ONLY predicates that exist in the provided Prolog knowledge base
- Return only the Prolog query
- Do not use ?-.
- If no matching predicate exists, return fail

Examples:

Question: Diagnose the patient
Output: diagnose

Question: Does the patient have diabetes?
Output: diabetes

User asks if the patient has diabetes:
diagnose(diabetes)

User asks what the symptoms of diabetes are:
symptoms(diabetes, Symptoms)

User asks what the criteria for diabetes are:
criteria(diabetes, Criteria)

User asks what diseases can be diagnosed:
possible_diagnoses(Diagnoses)

User asks about prediabetes:
diagnose(prediabetes)

User asks for prediabetes criteria:
criteria(prediabetes, Criteria)

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
