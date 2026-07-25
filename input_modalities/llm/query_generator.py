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

    - NEVER call ask_boolean, ask_numeric, ask_string, ask_category, ask_range,
      ask_duration, ask_multiple_category, ask_multi_structured_input,
      or ask_multi_attribute_entity directly in the query. These are internal
      input-collection primitives used INSIDE the knowledge base's own rules,
      not queryable facts - calling them directly passes a bare Prolog atom
      where a natural-language question string is expected, which breaks the
      dialogue. 
      Call a public domain predicate that represents the user's intent.
      Do not call internal input-collection or implementation-helper predicates.
      
- Variables must start with uppercase letters.

- Do not use natural language words as variables.


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

    # The model occasionally writes the query as if typed at the
    # Prolog REPL (leading "?- "), which isn't valid as a bare goal
    # passed to janus.query_once.
    if query.startswith("?-"):
        query = query[2:].strip()


    print(
        "Generated query:",
        query
    )


    return query
