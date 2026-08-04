
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
