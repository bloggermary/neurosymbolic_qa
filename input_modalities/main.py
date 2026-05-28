import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result


# user interaction

def ask(question: str) -> str:
    return input(question).strip().lower()


# main pipeline

if __name__ == "__main__":

    # step 1 — Load medical text
    with open("data/snippets/diabetes.txt") as f:
        medical_text = f.read()

    # step 2 — Generate Prolog KB
    generated_kb = generate_prolog_kb(medical_text)

    # step 3 — Save KB (IMPORTANT: consistent path)
    kb_path = "prolog/generated_kb/diabetes_diagnosis.pl"

    with open(kb_path, "w") as f:
        f.write(generated_kb)

    # step 4 — ALWAYS reset Prolog state BEFORE loading KB
    # (prevents old definitions like diagnose/0 vs diagnose/1 confusion)
    try:
        janus.query_once("retractall(known(_, _)).")
    except:
        pass

    # step 5 — ALWAYS reload KB before every run
    janus.consult(kb_path)

    # step 6 — Ask user question
    user_question = input("Ask a medical question: ")

    # step 7 — Generate Prolog query (must be valid Prolog goal)
    query = generate_query(user_question).strip()

    print("\nGenerated Query:", query)

    # step 8 — SAFETY CHECK (prevents obvious crashes)
    if not query:
        print("\nError: Empty query generated.")
        exit()

    # step 9 — Execute query (correct Janus usage)
    try:
        q = janus.query_once(query + ".")
    except Exception as e:
        print("\nProlog execution error:", e)
        print("Check if your query matches your KB predicates.")
        exit()

    # step 10 — Translate result safely
    try:
        final_answer = translate_result(q)
    except Exception:
        final_answer = str(q)

    # step 11 — Output
    print("\nFinal Answer:")
    print(final_answer)