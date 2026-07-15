from llm.client import client


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

GENERAL REQUIREMENTS:
- Output ONLY Prolog code.
- Do not use markdown.
- Do not add explanations.
- The code must run in SWI-Prolog.
- The code must be compatible with SWI-Prolog + Janus.
- Use logical predicates and rules only.
- Avoid singleton variables.
- Do not create unnecessary predicates.
- Ask only the minimum information necessary to reach a conclusion.

REASONING REQUIREMENTS:
- The knowledge base should support diagnosis, classification, and follow-up questioning.
- Stop asking questions as soon as the available evidence is sufficient.
- Do not ask additional criteria after a conclusion is already justified.
- Use the simplest valid reasoning path.

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

ask_scale(Question, Value) :-
    py_call(prolog_bridge:ask_scale(Question), Value).


MODALITY RULES:

Use:
- ask_boolean for yes/no questions
- ask_numeric for measurements and numbers
- ask_duration for time durations
- ask_range for bounded numeric intervals
- ask_scale for ratings from 1-10
- ask_category for fixed choices
- ask_string for free text

PREDICATE DESIGN:

Create clear public predicates.

For diagnosis:
- diagnose/1 should be the main workflow predicate.
- diabetes/0 should answer whether diabetes is logically true.
- prediabetes/0 should answer whether prediabetes is true.
- low_risk/0 should answer whether criteria are not met.

For specific criteria:
Create predicates representing the medical criteria.

Example:

fasting_glucose_mgdl(Value)

diabetes_positive_by_fasting_glucose

diabetes_positive_by_hba1c


IMPORTANT:
- diagnose/1 should use the minimum required questions.
- diagnose/1 should stop once a diagnosis is justified.
- Do not force every diagnostic criterion to be checked.

OUTPUT:
Return only executable Prolog code.

Medical Text:

{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()