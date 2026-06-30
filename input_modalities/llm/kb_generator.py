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
- After each answer, check whether the source text already provides sufficient evidence.
- Stop asking follow-up questions as soon as a diagnosis, exclusion, or classification is justified.
- Ask additional criteria only when the current evidence is insufficient.

JANUS USER INTERACTION:
- The generated knowledge base MUST start with:
    :- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value). 

ask_category(Question, Categories, Answer) :-
    py_call(main:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(main:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(main:ask_duration(Question), Value).  

ask_category_multiple(Question, Categories, Answers) :-
    py_call(main:ask_category_multiple(Question, Categories), Answers).

ask_multi_attribute_entity(Question, Entity, Fields, Result) :-
    py_call(main:ask_multi_attribute_entity(Question, Entity, Fields), Result).

ask_multi_structured_input(Question, Mode, Groups, Result) :-
    py_call(main:ask_multi_structured_input(Question, Mode, Groups), Result).
    
  

- The predicate diagnose/1 must ask all available diagnostic criteria before producing a result.
- If the user asks for an overall diagnosis, screening result, or asks generally whether the patient is diabetic, use the main entry predicate diagnose if it exists.
- If the user asks specifically whether diabetes is logically true, use diabetes if it exists
- If the user asks specifically about prediabetes, use prediabetes if it exists
- If the user asks specifically about low risk, use low_risk if it exists
- If the user asks about a concrete criterion and a matching predicate exists, use that predicate
- If several attributes of the same entity (e.g. medication, allergy, implanted device) need to be collected together, use ask_multi_attribute_entity/4. 
- If structured multi-value input is required:
    Use mode = sequence for ordered events.
    Use mode = ranking for prioritized items.
    Use mode = grouping together with a predefined list of groups.
- Prefer the most specific predicate that answers the question
- Prefer diagnose only for overall diagnostic workflows, because diagnose may ask all required user questions


Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
