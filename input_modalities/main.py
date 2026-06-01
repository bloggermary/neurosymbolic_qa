import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result


KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"


# -------------------------
# User interaction bridge
# -------------------------
def ask(question: str) -> str:
    """
    Called from Prolog via Janus (py_call).
    This is the symbolic ↔ neural interaction point.
    """
    return input(question + " ").strip().lower()


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

    # STEP 3 — user input
    user_question = input("Ask a medical question: ").strip()

    # STEP 4 — NL → Prolog query (LLM)
    query = generate_query(user_question).strip()
    query = query.split("(")[0].strip()

    print("\n[Generated Prolog Query]:", query)

    # STEP 5 — symbolic reasoning
    try:
        result = run_reasoning(query)
    except Exception as e:
        print("\nProlog execution error:", e)
        exit()

    print("\n[Raw Prolog Result]:", result)

    # STEP 6 — Prolog → natural language
    try:
        final_answer = translate_result(
            user_question,
            query,
            result
        )
    except Exception as e:
        print("\nTranslation fallback triggered:", e)
        final_answer = str(result)

    # STEP 7 — output
    print("\nFinal Answer:")
    print(final_answer)