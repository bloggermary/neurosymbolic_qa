from llm.client import client


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

GENERAL REQUIREMENTS:
- Return ONLY Prolog code.
- Do not use markdown or explanations.
- The code must run in SWI-Prolog with Janus.
- Use only information grounded in the supplied text.
- Use logical predicates and rules only.
- Avoid singleton variables.
- Do not create unnecessary predicates.
- Ask only the minimum information necessary to reach a conclusion.
- Stop asking follow-up questions as soon as a diagnosis, exclusion, or classification is justified.
- Ask additional criteria only when the current evidence is insufficient.
- Use lowercase snake_case for every generated predicate name,
  atom identifier, dictionary key, field key, and internal identifier.

REASONING REQUIREMENTS:
- The knowledge base should support diagnosis, classification, and follow-up questioning.
- Ask only as much as is genuinely needed to reach a confident, well-justified
  conclusion A real clinical dialogue is adaptive and stops once enough evidence exists,
  not an exhaustive questionnaire that works through everything available.
- see JANUS RESULT SAFETY.
  Do not invent clinical questions that aren't grounded in the provided text.

  QUESTION RULES:
- Every question must be complete and natural language suitable for a user.
- Ask only information needed by reachable reasoning rules.
- Stop asking as soon as a conclusion is justified.
- Do not ask an exhaustive checklist merely because information appears
  in the source text.

JANUS USER INTERACTION:

The generated knowledge base MUST start with:

:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(prolog_bridge:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(prolog_bridge:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(prolog_bridge:ask_string(Question), Value).

ask_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(prolog_bridge:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(prolog_bridge:ask_duration(Question), Value).

ask_multiple_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_multiple_category(Question, Categories), Answer).

ask_multi_structured_input(Question, Mode, Structure, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Structure), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).


MODALITY RULES:

Use:
- ask_boolean for yes/no questions
- ask_numeric for measurements and numbers
- ask_duration for time durations
- ask_range for bounded numeric intervals (including ratings/severity
  scores from 1-10, since those are also bounded-interval answers)
- ask_category for exactly one fixed choice
- ask_string for free text
- Use ask_multi_structured_input only for sequence, ranking, or grouped data.
- Use ask_multi_attribute_entity only for several attributes of one entity.
- Use structured modalities only when they are clearly supported by the text.

CRITICAL - NUMERIC SAFETY:
- ask_numeric, ask_duration, and ask_range return numeric values compatible
  with Python floats. 
- Do not require integer(Value). 
- Use numeric comparisons or round/truncate when an integer is genuinely required.
If you need a whole-number count for something like "how many entries to
collect", compare with >= /=< or convert explicitly with round/1 or
truncate/1 - do not test the term's type.

PROLOG AND JANUS SAFETY:

1. ARITHMETIC SAFETY: with is/2
- The right side of is/2 must contain only arithmetic expressions.
- Never place comparisons, atoms, or control constructs such as
  ==, \\=, ->, or ; inside is/2.
- Use ordinary if-then-else with unification instead.

GOOD:
    ( Flag == true -> Count = 1 ; Count = 0 )

BAD:
    Count is (Flag == true -> 1 ; 0)


2. STRUCTURED MODALITY SAFETY:
- ask_multiple_category is for selecting several options and returns a list.
- ask_multi_structured_input is only for sequence, ranking, or grouped data.
- ask_multi_attribute_entity is only for several attributes of one entity.
- Use these modalities only when clearly supported by the source text.
- Do not use them merely to demonstrate available modalities.

For ask_multi_attribute_entity, Fields must be plain lists:

    [
        [name, 'What is the medication name?', string],
        [dose_mg, 'What is the dose in mg?', float]
    ]

Do not use custom terms such as field(...).


3. Boolean handling
ask_boolean/1 succeeds for yes and fails for no. It does not return a value.

To store the result, always use:

    ( ask_boolean('Complete question?')
      -> Flag = true
      ;  Flag = false
    )


4. Reachable reasoning
- Do not generate placeholder, dummy, or unreachable predicates.
- Create exactly one diagnose/1 predicate for the complete workflow.
- Every ask_* call must belong to real reasoning logic.


5. Janus-safe return values
Query result variables may contain only:
- atoms
- strings
- numbers
- lists
- Key-Value pairs
- SWI-Prolog dictionaries

Never return custom compound terms such as:

    diagnosis_summary(...)
    symptom(...)
    fatigue_severity(...)

GOOD:
    diagnose(diabetes)

GOOD:
    diagnose(_{{
        verdict: diabetes,
        evidence: random_glucose
    }})

BAD:
    diagnose(diagnosis_summary(diabetes, random_glucose))


PREDICATE DESIGN:
- Create exactly one diagnose/1 predicate for the complete workflow.
- Do not create placeholder, dummy, or unreachable predicates.
- Create one independently callable predicate per specific criterion.
- Each criterion predicate must ask internally for all values it needs.
- Do not require input arguments that only diagnose/1 can prepare.
- diagnose/1 may call criterion predicates and stop after a decisive result.


Medical Text:

{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
