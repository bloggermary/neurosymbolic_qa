import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result

from modalities.router import route_boolean, route_numeric, route_string, route_scale, route_frequency, route_medication, route_medical_history, route_family_history

KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"


# -------------------------
# User interaction bridge
# -------------------------
def ask_boolean(question: str) -> bool:
    return route_boolean(question)


def ask_numeric(question: str) -> float:
    return route_numeric(question)


def ask_string(question: str) -> str:
    return route_string(question)


def ask_scale(question:str, scale_min: int, scale_max: int) -> int:
    return route_scale(question, scale_min, scale_max)


def ask_frequency(question:str, options: list[str]) -> str:
    return route_frequency(question, options)


def ask_medication(question:str, options: list[str]) -> list[str]:
    return route_medication(question, options)


def ask_medical_history(question:str, options: list[str]) -> list[str]:
    return route_medical_history(question, options)


def ask_family_history(question:str, options: list[str]) -> dict: 
    return route_family_history(question, options)


# -------------------------
# PIPELINE STEP 1: Build KB
# -------------------------
def build_knowledge_base():
    with open("data/snippets/diabetes.txt", "r", encoding="utf-8") as f:
        medical_text = f.read()

    kb_code = generate_prolog_kb(medical_text)

    with open(KB_PATH, "w", encoding="utf-8") as f:
        f.write(kb_code)


# -------------------------
# PIPELINE STEP 2: Load Prolog
# -------------------------
def load_prolog():
    janus.consult(KB_PATH)


# -------------------------
# PIPELINE STEP 3: Query execution
# -------------------------
def run_reasoning(query: str):
    if not query:
        raise ValueError("Empty Prolog query generated")

    # ensure clean Prolog call
    query = query.rstrip(".").strip()

    return janus.query_once(query)


# -------------------------
# MAIN PIPELINE
# -------------------------
if __name__ == "__main__":

    # STEP 1 — build symbolic KB using LLM
    build_knowledge_base()

    # STEP 2 — load Prolog engine
    load_prolog()

    # STEP 3 — read generated KB code
    with open(KB_PATH, "r", encoding="utf-8") as f:
        prolog_code = f.read()

    # STEP 4 — user input
    user_question = input("Ask a medical question: ").strip()

    # STEP 5 — NL → Prolog query (LLM)
    query = generate_query(
        user_question, prolog_code).strip()

    print("\n[Generated Prolog Query]:", query)

    # STEP 6 — symbolic reasoning
    try:
        result = run_reasoning(query)
    except Exception as e:
        print("\nProlog execution error:", e)
        exit()

    print("\n[Raw Prolog Result]:", result)

    # STEP 7 — Prolog → natural language
    try:
        final_answer = translate_result(
            user_question,
            query,
            result
        )
    except Exception as e:
        print("\nTranslation fallback triggered:", e)
        final_answer = str(result)

    # STEP 8 — output
    print("\nFinal Answer:")
    print(final_answer)