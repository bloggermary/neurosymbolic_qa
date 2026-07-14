from llm.client import client


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

GENERAL REQUIREMENTS:
- Output ONLY Prolog code (no explanations)
- NO markdown (no ``` blocks)
- Must include ask(Question) usage for user interaction
- Use logical predicates only
- Ensure rules are consistent and executable in SWI-Prolog
- Must be compatible with SWI-Prolog + Janus
- Do not generate clauses with singleton variables. If a question's answer is not needed
  for the result, do not ask it at all.
- Ask only the minimum information necessary to reach a conclusion.
- Stop asking follow-up questions as soon as a diagnosis, exclusion, or classification is justified.
- Ask additional criteria only when the current evidence is insufficient.

KEY-BASED FOLLOW-UP REQUIREMENT:
- Every user interaction predicate MUST include a stable semantic key.
- The key MUST be a lowercase snake_case Prolog atom.
- The key MUST describe the medical criterion, not the wording of the question.
- Do NOT use vague keys like key, question_1, followup_1, value, answer, symptom, criterion.
- Do NOT use an unbound variable named Key in py_call.
- The Key argument must always be passed into the ask_* predicate and then forwarded to Python.

When the source criterion requires a yes/no condition,
use ask_boolean.

When the source criterion requires a measured number,
use ask_numeric.

When the source criterion explicitly defines lower and upper
integer bounds for a rating or score, use ask_range.

When the source criterion concerns elapsed time in days,
weeks, months, or years, use ask_duration.

When the source defines a fixed set of named alternatives,
use ask_category.

When unrestricted text is required, use ask_string.

JANUS USER INTERACTION:
- The generated knowledge base MUST start with:
    :- use_module(library(janus)).

ask_boolean(Key, Question) :-
    py_call(main:ask_boolean(Key, Question), true).

ask_numeric(Key, Question, Value) :-
    py_call(main:ask_numeric(Key, Question), Value).

ask_string(Key, Question, Value) :-
    py_call(main:ask_string(Key, Question), Value).

ask_category(Key, Question, Categories, Answer) :-
    py_call(main:ask_category(Key, Question, Categories), Answer).

ask_range(Key, Question, Start, Stop, Value) :-
    py_call(main:ask_range(Key, Question, Start, Stop), Value).

ask_duration(Key, Question, Value) :-
    py_call(main:ask_duration(Key, Question), Value).    


- If one criterion is sufficient according to the source text, the rule may stop after that criterion succeeds.
- Availability of a test result is not a medical criterion. The measured numeric value is the criterion.
- If the user asks specifically about prediabetes, use prediabetes if it exists
- If the user asks specifically about low risk, use low_risk if it exists
- If the user asks about a concrete criterion and a matching predicate exists, use that predicate
- Prefer the most specific predicate that answers the question
- Prefer diagnose only for overall diagnostic workflows, because diagnose may ask all required user questions


Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()