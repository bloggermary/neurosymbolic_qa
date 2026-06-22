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

JANUS USER INTERACTION:
- The generated knowledge base MUST start with:
    :- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value). 

ask_scale(Question, ScaleMin, ScaleMax, Value) :-
    py_call(main:ask_scale(Question, ScaleMin, ScaleMax), Value).

ask_frequency(Question, Options, Value) :-
    py_call(main:ask_frequency(Question, Options), Value).

ask_medication(Question, Options, Value) :-
    py_call(main:ask_medication(Question, Options), Value).

ask_medical_history(Question, Options, Value) :-
    py_call(main:ask_medical_history(Question, Options), Value).

ask_family_history(Question, Options, Value) :-
    py_call(main:ask_family_history(Question, Options), Value).
    

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


Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def ask_scale(question: str, min_value: int = 1, max_value: int = 10) -> int:
    """Ask a numeric rating scale (e.g. symptom severity from 1 to 10).
    Called from Prolog via py_call(main:ask_scale(Question, ScaleMin, ScaleMax), Value)."""
    
    while True:
        prompt = f"{question} ({min_value}-{max_value}): "
        answer = input(prompt).strip().lower()

        if answer.isdigit():
            value = int(answer)
            if min_value <= value <= max_value:
                return value

        print(f"Value must be between {min_value} and {max_value}.")


def ask_frequency(question: str, options: list[str] = None) -> str:
    """Ask a frequency question (e.g. how often do you experience X?).
    Called from Prolog via py_call(main:ask_frequency(Question, Options), Value)."""
    
    if options is None:
        options = ["never", "rarely", "sometimes", "often", "daily"]  # Example options
    
    while True:
        prompt = f"{question} ({', '.join(options)}): "
        answer = input(prompt).strip().lower()

        if answer in options:
            return answer
        
        print(f"Please answer with one of the following: {', '.join(options)}.")


def ask_medication(question: str) -> list[str]:
    """Ask about current medications with free-text list input.
    Called from Prolog via py_call(main:ask_medication(Question), Value)."""
    
    answer = input(f"{question} (comma-separated): ").strip()
    
    if not answer:
        print("Please enter at least one medication, or 'none' if not taking any.")
        return ask_medication(question)
    
    if answer.lower() in ["none", "no", "n/a", "not taking any"]:
        return []
    
    return [med.strip() for med in answer.split(",") if med.strip()]


def ask_medical_history(question:str, options: list[str]) -> list[str]:
    """Ask for medical history as multiple choice.
    Called from Prolog via py_call(main:ask_medical_history(Question, Options), Answer)."""
    
    print(f"\n{question}\nHave you ever been diagnosed with any of the following conditions? ")  
    
    for opt in options:
        print(f"- {opt}")
    
    while True:
        answer = input("\nPlease answer as a comma-separated list of conditions you have been diagnosed with, or 'none' if not.").strip().lower()

        if answer.lower() in ["none", "no", "n/a", "never"]:
            return []
        
        selected = [a.strip() for a in answer.split(",") if a.strip()]
        valid = [s for s in selected if s in [o.lower() for o in options]]

        if valid:
            return valid
        
        print("Please enter valid conditions from the list, or 'none' if not diagnosed with any.")  
    

def ask_family_history(question:str, options: list[str]) -> dict:
    """Ask for family medical history with follow-up questions.
    Called from Prolog via py_call(main:ask_family_history(Question, Options), Answer)."""
    
    print(f"{question}\n")

    results = {}

    for condition in options:
        answer = input(f"{condition} (yes / no / don't know): ").strip().lower()

        if answer not in ["yes", "no", "don't know", "dont know", "idk"]:
            print("Please answer with 'yes', 'no', or 'I don't know'.")
            return ask_family_history(question, options)

        entry = {
            "has_family_history": answer == "yes",
        }

        if answer == "yes":
            who = input(f"Who in your family has {condition}? (e.g. mother, father, sibling): ").strip().lower()
            entry["family_member"] = who

        results[condition.lower()] = entry

    return results
