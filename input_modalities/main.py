import janus_swi as janus
from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result

# user interaction

def ask(question: str) -> str:
    return input(question).strip().lower()

# main pipeline

if __name__ == "__main__":

    # step 1 — load medical text
    with open("data/snippets/diabetes.txt") as f:
        medical_text = f.read()

    # step 2 — generate Prolog KB
    generated_kb = generate_prolog_kb(medical_text)

    # step 3 — save generated KB
    with open("prolog/generated_kb/diabetes_diagnosis.pl", "w") as f:
        f.write(generated_kb)

    # step 4 — load KB into Prolog
    janus.consult("prolog/generated_kb/diabetes_diagnosis.pl")

    # step 5 — ask user question
    user_question = input("Ask a medical question: ")

    # step 6 — generate Prolog query
    query = generate_query(user_question)

    print(f"\nGenerated Query: {query}")

    # step 7 — execute query
    result = janus.query_once(query)

    # step 8 — translate response
    final_answer = translate_result(result)

    # step 9 — output final answer
    print("\nFinal Answer:")
    print(final_answer)