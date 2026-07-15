from llm.client import client


def generate_query(question: str, prolog_code: str) -> str:
    prompt = f"""

    You are an expert SWI-Prolog query generator.

    Convert the user question into exactly ONE executable SWI-Prolog query.

    RULES:

    - Return ONLY the Prolog query.

    - No explanations.

    - The query must be valid SWI-Prolog.

    - Use only predicates existing in the knowledge base.

    - Variables must start with uppercase letters.

    - Do not use natural language words as variables.

    QUERY SELECTION:

    Use diagnose/1 when:

    - the user asks generally about diagnosis

    - the user asks if the patient is diabetic

    - the user asks for an overall classification

    Use diabetes/0 when:

    - the user asks whether diabetes is true

    Use prediabetes/0 when:

    - the user asks specifically about prediabetes

    Use low_risk/0 when:

    - the user asks about low risk

    Use specific criterion predicates only when:

    - the user explicitly asks about one criterion

    Available predicates:

    - diagnose/1

    - diabetes/0

    - prediabetes/0

    - low_risk/0

    - diabetes_positive/0

    - prediabetes_positive/0

    - diabetes_positive_by_random_glucose/0

    - diabetes_positive_by_fasting_glucose/0

    - diabetes_positive_by_ogtt/0

    - diabetes_positive_by_hba1c/0

    - random_glucose_mgdl/1

    - fasting_glucose_mgdl/1

    - fasting_duration_hours/1

    - ogtt_2hr_mgdl/1

    - hba1c_percent/1

    Knowledge Base:

    {prolog_code}

    Question:

    {question}

    """


    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )


    query = (
        response
        .choices[0]
        .message
        .content
        .strip()
        .rstrip(".")
    )


    print(
        "Generated query:",
        query
    )


    return query