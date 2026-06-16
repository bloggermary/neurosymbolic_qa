from llm.client import client

def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are a Prolog query generator.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

GENERAL REQUIREMENTS:
- Output ONLY Prolog code
- Do not use markdown
- The output must be valid and executable SWI-Prolog code
- The knowledge base must be compatible with SWI-Prolog and Janus
- Do not assume fixed diseases, fixed predicates, or fixed diagnosis names
- Derive predicate names, rule names, and diagnostic concepts only from the given input text
- Use meaningful, general predicate names based on the content of the text
- Do not use read/1, write/1, nl/0, or direct Prolog console input
- Do not ask the user for measurement units if the medical text already gives a threshold with a unit.
- Choose one unit from the text and ask the numeric value in that unit.
- Do not represent explanations as compound Prolog terms such as reason(...).
- If a rule needs to return a reason, return atoms or strings only.
- If multiple symptoms are mentioned, collect all symptom answers first before evaluating the symptom pattern.
- Do not stop after the first positive symptom.
- Prefer simple atoms such as gelegenheits_plasmaglukose instead of reason(gelegenheits_plasmaglukose).

JANUS USER INPUT BRIDGE:
The generated knowledge base must start with this code exactly once:

:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value).

USER INPUT MODALITIES:
Use typed user-input predicates according to the semantic type of the required patient-specific information.

- Use ask_boolean/1 for presence/absence information, yes/no criteria, symptoms, conditions, or true/false facts.
- Use ask_numeric/2 for measured values, thresholds, scores, age, duration, quantities, concentrations, percentages, or any numeric comparison.
- Use ask_string/2 for categories, labels, locations, types, names, severity levels, or other textual values.

PROLOG CORRECTNESS RULES:
- Every variable must be introduced before it is used.
- Every variable used in a numeric comparison must first be bound by ask_numeric/2 or another predicate.
- Every variable used in a textual comparison must first be bound by ask_string/2 or another predicate.
- Boolean criteria should be represented by calling ask_boolean/1 directly as a goal.
- Avoid singleton variables.
- Do not create variables that occur only once.
- Do not use if-then-else constructs with unbound variables.
- Do not compare unbound variables.
- Do not invent patient facts.
- If patient-specific information is needed, ask for it through ask_boolean/1, ask_numeric/2, or ask_string/2.
- Output variables must reflect the collected user input and remain available to later predicates and query results.
- - Output variables must reflect the collected user input and remain available to later predicates and query results.

REASONING STRUCTURE:
- Represent each criterion as a separate reusable predicate when possible.
- Represent final conclusions as logical rules over those criteria.
- Do not stop after the first positive criterion if the text requires multiple criteria to be checked.
- If the text describes alternative sufficient criteria, model them as separate Prolog rules or separate criterion predicates.
- If the text describes combined criteria, model them with conjunctions.
- Keep the generated rules simple and executable.


Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()