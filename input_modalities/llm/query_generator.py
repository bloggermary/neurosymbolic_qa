from llm.client import client


def generate_query(question: str, prolog_code: str) -> str:
    prompt = f"""

    You are an expert SWI-Prolog query generator.

    Convert the user question into exactly ONE executable SWI-Prolog query.

    RULES:

    - Return ONLY the Prolog query.

    - No explanations.

    - The query must be valid SWI-Prolog.

    - Use only predicates existing in the knowledge base below - never
      invent a predicate name, and never assume a name or structure
      from a different domain or a different knowledge base. Ground
      every choice in exactly what this specific knowledge base
      actually defines.

    - NEVER call ask_boolean, ask_numeric, ask_string, ask_category, ask_range,
      ask_duration, ask_multiple_category, ask_multi_structured_input,
      or ask_multi_attribute_entity directly in the query. These are internal
      input-collection primitives used INSIDE the knowledge base's own rules,
      not queryable facts - calling them directly passes a bare Prolog atom
      where a natural-language question string is expected, which breaks the
      dialogue. Always call a real diagnostic/domain predicate instead and
      let that predicate call ask_* internally.

    - Variables must start with uppercase letters.

    - Do not use natural language words as variables.

    QUERY SELECTION:

    Use the knowledge base's direct status predicate (typically a
    0-argument predicate representing the overall condition or
    outcome) when the user asks a DIRECT factual yes/no question about
    the patient's status as a whole, without asking about the process
    or naming one specific criterion. This wants a single true/false-
    style predicate, not the full workflow.

    Use the knowledge base's main interactive workflow predicate
    (typically its single argument is a free variable capturing the
    overall result) when the user asks about the PROCESS or WORKFLOW
    itself, rather than a direct yes/no on one specific status - for
    instance, questions asking what should be evaluated, how a
    determination should be made, or which procedure/screening applies,
    or that otherwise don't commit in advance to one specific outcome.

    Use a specific criterion predicate (however the knowledge base
    names the predicate for one particular measurement or rule) when
    the user asks whether ONE particular measurement or criterion is
    diagnostic on its own, especially when the question already states
    a concrete value for it.

    If the question already STATES a specific numeric value for a
    measurement, bind that value into the query as its own goal
    ALONGSIDE the criterion check, instead of only calling the
    criterion predicate alone - the value is already known, it
    shouldn't be asked for again. If no concrete value is stated in
    the question, just call the criterion or measurement predicate
    with an unbound variable as usual.

    If the user is asking WHICH measurement or value is relevant or
    should be checked (rather than asking to evaluate a criterion),
    query the measurement predicate itself - not a diagnostic criterion
    predicate and not the main workflow predicate.

    If the user asks about one or more specific symptoms or findings
    the knowledge base represents as their own individual predicates,
    call the matching predicate(s) directly (conjoining more than one
    if the question names more than one) rather than the main workflow
    predicate - a question about a specific symptom or finding isn't
    asking for an overall diagnosis.

    If the question is really asking whether ONE SPECIFIC outcome would
    be reached via the general workflow, bind that outcome as the
    workflow predicate's argument instead of leaving it as a free
    variable. Use a free variable only when the question doesn't
    already imply which specific outcome is being asked about.

    If the question explicitly names more than one measurement as part
    of a broader diagnostic question, make each named measurement its
    own explicit goal in the query, conjoined with whichever
    diagnostic predicate you use - even if that predicate would also
    check them internally - so the query reflects every specific
    measurement the user named.

    NEVER call a predicate that takes 3 or more arguments directly in
    the query, and NEVER pass an anonymous variable (_) or a fresh
    unbound variable as an argument just to satisfy an arity you don't
    have a real value for. Predicates with several arguments are
    typically internal helpers that assume earlier context already
    bound those arguments - calling them directly from a top-level
    query with made-up placeholders will crash with an uninstantiated-
    argument error. If the question doesn't map cleanly onto a simple 0
    or 1-argument predicate, fall back to the main workflow predicate
    with a free variable rather than guessing at a complex predicate's
    internal calling convention.

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
