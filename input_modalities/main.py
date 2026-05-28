import janus_swi as janus

from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result


# user interaction
def ask(question: str) -> str:
    return input(question).strip().lower()


if __name__ == "__main__":

    # step 1 — Load medical text
    with open("data/snippets/diabetes.txt") as f:
        medical_text = f.read()

    # step 2 — Generate Prolog KB
    generated_kb = generate_prolog_kb(medical_text)

    # step 3 — Save KB
    kb_path = "prolog/generated_kb/diabetes_diagnosis.pl"

    with open(kb_path, "w") as f:
        f.write(generated_kb)

    # MUST append FIRST before consulting
    with open(kb_path, "a") as f:
        f.write("""

    diagnose(Result) :-
        ( diagnosis(_, diabetes) ->
            Result = diabetes
        ; diagnosis(_, prediabetes) ->
            Result = prediabetes
        ; possible_diabetes(_) ->
            Result = possible_diabetes
        ;   Result = no_diabetes
        ).
    """)

    janus.consult(kb_path)

    # step 5 — reset Prolog state
    try:
        janus.query_once("retractall(known(_, _)).")
    except:
        pass

    # step 6 — load KB
    janus.consult(kb_path)

    # step 7 — ask user
    user_question = input("Ask a medical question: ")

    # step 8 — generate query
    query = generate_query(user_question).strip()

    print("\nGenerated Query:", query)

    if not query:
        print("\nError: Empty query generated.")
        exit()

    # step 9 — clean query
    query = query.rstrip(".")

    # step 10 — execute Prolog (ONLY ONCE)
    try:
        result = janus.query_once(query + ".")
    except Exception as e:
        print("\nProlog execution error:", e)
        exit()

    # step 11 — translate result
    try:
        final_answer = translate_result(result)
    except Exception:
        final_answer = str(result)

    # step 12 — output
    print("\nFinal Answer:")
    print(final_answer)