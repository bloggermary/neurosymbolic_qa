from llm.client import client

# FEEDBACK: This does not actually result in the Python ask method being called through Janus.
# This results in the internal Prolog input mechanism being triggered.
# Please look closely at the template I provided you.
# You must instruct the LLM how it can trigger the Python function.
# Exampel prompt:
# -----------------
# Add and use the following Prolog predicate to ask a yes/no question to the user through the Janus integration.
# ask(Question) :-
#    py_call(main:ask(Question), yes).


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

STRICT REQUIREMENTS:
- Output ONLY Prolog code (no explanations)
- NO markdown (no ``` blocks)
- Must include ask(Question) usage for user interaction
- Must define:
    - diagnose/1
    - diabetes/1
    - prediabetes/1
- Use logical predicates only
- Ensure rules are consistent and executable in SWI-Prolog
- Must be compatible with SWI-Prolog + Janus

- The generated knowledge base MUST start with:
    :- use_module(library(janus)).

- for user interaction:
    ask(Question) :-
        py_call(main:ask(Question), yes)

- The predicate diagnose/1 must ask all available diagnostic criteria before producing a result.
- Do not stop after the first positive criterion.
- Collect all answers first, then evaluate the diagnosis.
- If the user asks for an overall diagnosis, screening result, or asks generally whether the patient is diabetic, use the main entry predicate diagnose if it exists.
- If the user asks specifically whether diabetes is logically true, use diabetes if it exists
- If the user asks specifically about prediabetes, use prediabetes if it exists
- If the user asks specifically about low risk, use low_risk if it exists
- If the user asks about a concrete criterion and a matching predicate exists, use that predicate
- Prefer the most specific predicate that answers the question
- Prefer diagnose only for overall diagnostic workflows, because diagnose may ask all required user questions
- Generate Prolog predicates for:

    diagnosis rules
    symptoms
    diagnostic criteria
    diseases mentioned in the text

Example:

symptom(diabetes, excessive_thirst).
symptom(diabetes, excessive_urination).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease,S), Symptoms).

criterion(diabetes, random_glucose).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease,C), Criteria).

Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
