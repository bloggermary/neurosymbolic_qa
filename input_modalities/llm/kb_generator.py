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
- For the *numeric diagnostic threshold* (which single measurement proves diabetes),
  stop asking further numeric criteria as soon as one threshold is met - do not force
  every numeric criterion to be checked once a conclusion is already justified.
- Use the simplest valid reasoning path for the numeric threshold check itself.
- HOWEVER: the source text describes this domain as explicitly multi-modal (numeric,
  boolean, range, categorical, and temporal/duration data all appear in it). The main
  diagnose/1 workflow MUST also collect the supporting clinical picture described in
  the text - not just the numeric threshold - because that supporting evidence is part
  of what a real clinical dialogue would gather, and because this system is built to
  demonstrate multi-modal reasoning, not numeric-only reasoning. Concretely, diagnose/1
  (and diabetes/0 when used as the general entry point) should, in addition to the
  numeric threshold check:
    - ask_boolean for each symptom explicitly mentioned in the text (e.g. excessive
      thirst, excessive urination, fatigue, blurred vision)
    - ask_category for medication status and any categorical history mentioned in the
      text (e.g. insulin / oral antidiabetics / corticosteroids / none)
    - ask_range or ask_duration for any threshold/temporal detail mentioned in the text
      (e.g. hours of fasting before a glucose sample)
  Collect this alongside the numeric verdict in one result term (e.g.
  diagnosis_summary(Verdict, SymptomsPresent, Medication, ...)) so the answer can
  reflect the full picture, not just a bare true/false. Do not invent clinical
  questions that aren't grounded in the provided text.

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

CRITICAL - ask_boolean/1 HAS NO OUTPUT ARGUMENT:
ask_boolean(Question) only succeeds (on "yes") or fails (on "no") - it does NOT bind
a value anywhere. To actually capture the yes/no answer into a variable, you MUST use
this exact if-then-else idiom:
    ( ask_boolean('Some question?') -> Flag = true ; Flag = false )
Writing `ask_boolean(Question), X = SomeVar` does NOT capture the answer - X/SomeVar
stay unbound, and the whole clause simply fails whenever the user answers "no" (with
no fallback), which breaks the entire diagnosis. Never write ask_boolean this way.

NEVER add placeholder, dummy, or "ensure predicate is referenced" clauses that exist
only to make ask_boolean/ask_numeric/etc appear used in the source. Every clause you
write must be part of real, reachable diagnostic logic. Do not write multiple
near-duplicate diagnose/1 clauses - write exactly ONE diagnose/1 clause that performs
the complete workflow.

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
- diagnose/1 should stop asking further NUMERIC threshold criteria once one of them
  alone already justifies the verdict (do not check every numeric criterion).
- diagnose/1 must still ALSO collect the supporting boolean symptoms, categorical
  medication/history, and any duration/range detail described in the text, every time -
  these are not part of the "stop early" rule, they are the multi-modal clinical
  picture this system is designed to demonstrate.

OUTPUT:
Return only executable Prolog code.

Medical Text:

{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()