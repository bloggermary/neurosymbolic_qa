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
      ask_duration, or ask_scale directly in the query. These are internal
      input-collection primitives used INSIDE the knowledge base's own rules,
      not queryable facts - calling them directly passes a bare Prolog atom
      where a natural-language question string is expected, which breaks the
      dialogue. Always call a real diagnostic/domain predicate instead (e.g.
      diagnose/1, diabetes/0, prediabetes/0, low_risk/0, or a specific
      criterion predicate) and let that predicate call ask_* internally.

    - Variables must start with uppercase letters.

    - Do not use natural language words as variables.

    QUERY SELECTION:

    Use diabetes/0 (or the equivalent boolean predicate for this
    domain, e.g. prediabetes/0, low_risk/0) when the user asks a
    DIRECT factual yes/no question about the patient's status:
    - "Is the patient diabetic?"
    - "Does the patient have diabetes mellitus?"
    - "Can diabetes be diagnosed using the available criteria?"
    These want a single true/false-style predicate, not the workflow.

    Use diagnose/1 when the user asks about the PROCESS or WORKFLOW
    itself, rather than a direct yes/no on one specific status:
    - "What predicate/workflow should be used to determine diabetes?"
    - "Should the patient be evaluated for diabetes?"
    - "How should diabetes classification be performed?"
    - questions explicitly mentioning "workflow", "procedure",
      "which criteria should be evaluated", "screening"
    diagnose/1 returns whichever of diabetes/prediabetes/low_risk
    applies, so use it when the question doesn't commit to one of
    those outcomes in advance.

    Use a specific criterion predicate (e.g.
    diabetes_positive_by_fasting_glucose) when the user asks whether
    ONE particular measurement or criterion is diagnostic, especially
    when the question already states a concrete value for it.

    If the question already STATES a specific numeric value for a
    measurement (e.g. "fasting glucose of 135 mg/dL", "HbA1c is
    6.9%"), bind that value into the query as its own goal ALONGSIDE
    the criterion check, instead of only calling the criterion
    predicate alone - the value is already known, it shouldn't be
    asked for again:
        fasting_glucose_mgdl(135), diabetes_positive_by_fasting_glucose
        hba1c_percent(6.9), diabetes_positive_by_hba1c
    If no concrete value is stated in the question, just call the
    criterion or measurement predicate with an unbound variable as
    usual (e.g. fasting_glucose_mgdl(Value)).

    If the user is asking WHICH measurement/lab value is relevant or
    should be checked (rather than asking to evaluate a criterion),
    query the measurement predicate itself, e.g. fasting_glucose_mgdl(Value)
    or hba1c_percent(Value) - not a diagnostic criterion predicate and
    not diagnose/1.

    If the user asks about specific symptoms (thirst, urination,
    fatigue, blurred vision, etc.), call the matching symptom
    predicate(s) directly (e.g. excessive_thirst, or
    excessive_thirst, excessive_urination for a question naming both)
    rather than diagnose/1 - symptom questions aren't asking for an
    overall diagnosis.

    If the question is really asking whether ONE SPECIFIC verdict
    (diabetes / prediabetes / low_risk) would be reached via the
    general workflow, bind that verdict as diagnose/1's argument
    instead of leaving it as a free variable:
        diagnose(diabetes)
        diagnose(prediabetes)
    Use a free variable (diagnose(Result)) only when the question
    doesn't already imply which specific verdict is being asked about.

    If the question explicitly names more than one measurement (e.g.
    both fasting glucose AND HbA1c) as part of a broader diagnostic
    question, make each named measurement its own explicit goal in the
    query, conjoined with whichever diagnostic predicate you use -
    even if that predicate would also check them internally - so the
    query reflects every specific measurement the user named:
        fasting_glucose_mgdl(F), hba1c_percent(H), diagnose(Result)

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
