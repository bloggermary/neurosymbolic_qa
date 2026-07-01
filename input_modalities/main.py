import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result

from modalities.router import (
    route_boolean,
    route_numeric,
    route_string,
    route_category,
    route_range,
    route_duration
)

# -------------------------
# Dialogue Layer (NEW)
# -------------------------
from dialogue.session_handler import SessionMemory
from dialogue.state_manager import StateManager
from dialogue.context_tracker import ContextTracker
from dialogue.followup_manager import FollowupManager
from dialogue.modality_handler import DialogueModalityHandler


KB_PATH = "prolog/generated_kb/diabetes_diagnosis.pl"


# -------------------------
# Dialogue Initialization
# -------------------------
session_memory = SessionMemory()
state_manager = StateManager()
context_tracker = ContextTracker(session_memory)
followup_manager = FollowupManager()
modality_handler = DialogueModalityHandler()


# -------------------------
# User interaction bridge
# -------------------------
def ask_boolean(question: str) -> bool:
    return route_boolean(question)


def ask_numeric(question: str) -> float:
    return route_numeric(question)


def ask_string(question: str) -> str:
    return route_string(question)


def ask_category(question: str, categories: list[str]) -> str:
    return route_category(question, categories)


def ask_range(question, start: int, stop: int):
    return route_range(question, start, stop)


def ask_category_multiple(question: str, categories: str, num_answers: int):
    pass


def ask_duration(question: str) -> int:
    return route_duration(question)



# PIPELINE STEP 1: Build KB

def build_knowledge_base():
    with open("data/snippets/diabetes.txt", "r", encoding="utf-8") as f:
        medical_text = f.read()

    kb_code = generate_prolog_kb(medical_text)

    with open(KB_PATH, "w", encoding="utf-8") as f:
        f.write(kb_code)



# PIPELINE STEP 2: Load Prolog

def load_prolog():
    janus.consult(KB_PATH)



# PIPELINE STEP 3: Query execution

def run_reasoning(query: str):
    if not query:
        raise ValueError("Empty Prolog query generated")

    query = query.rstrip(".").strip()
    return janus.query_once(query)



# MAIN PIPELINE

if __name__ == "__main__":

    # STEP 1 — build symbolic KB using LLM
    build_knowledge_base()


    # step 2 — load Prolog engine
    load_prolog()

    # step 3 — read generated KB code
    with open(KB_PATH, "r", encoding="utf-8") as f:
        prolog_code = f.read()

    # step 4 — user input
    user_question = input("Ask a medical question: ").strip()


    #  Dialogue Layer: Context Resolution

    resolved = context_tracker.resolve_context(user_question)
    enhanced_question = resolved["question"]

    # step 5 — NL → Prolog query (LLM)
    query = generate_query(enhanced_question, prolog_code).strip()

    print("\n[Generated Prolog Query]:", query)

    # step 6 — symbolic reasoning
    try:
        result = run_reasoning(query)
    except Exception as e:
        print("\nProlog execution error:", e)
        exit()

    print("\n[Raw Prolog Result]:", result)

    # step 7 — Prolog → natural language
    try:
        final_answer = translate_result(enhanced_question, query, result)
    except Exception as e:
        print("\nTranslation fallback triggered:", e)
        final_answer = str(result)


    #  Dialogue Layer: State + Memory Update


    state_manager.update(
        question=user_question,
        answer=final_answer,
        modality=None,
        prolog_query=query
    )

    session_memory.add({
        "question": user_question,
        "answer": final_answer,
        "modality": None,
        "prolog_query": query
    })

    # follow-up generation hook (stored externally if you add LLM later)
    followup_manager.store(user_question, [])


    # step 8 — Output

    response = {
        "answer": final_answer,
        "style": "default"
    }

    # adjust response based on modality (future extension)
    response = modality_handler.adjust_response_behavior(
        modality=None,
        response=response
    )

    print("\nFinal Answer:")
    print(response["answer"])