import janus_swi as janus
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

def read_prompt(filename: str) -> str:
    return Path("prompts", filename).read_text(encoding="utf-8")

# The user interaction method that is being called from Prolog in `diabetes_diagnosis.pl`
def ask(question: str) -> str:
    """Called from Prolog via py_call(diabetes_diagnosis:ask(Question), "yes")."""
    return input(question).strip().lower()

# TODO: Automatically generate `diabetes_diagnosis.pl` from medical text using an LLM
# TODO: Make sure that the automatically generated `diabetes_diagnosis.pl` uses the `ask` method below

def get_openai_client():
    load_dotenv()
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_diabetes_diagnosis_pl() -> None:
    medical_text = Path("medical_diabetes.txt").read_text(encoding="utf-8")

    prolog_code = medicaltext_to_prolog(medical_text)

# save prolog code in diabetes_diagnosis.pl
    Path("test_diabetes_diagnosis.pl").write_text(
        prolog_code,
        encoding="utf-8"
    )

# generate prolog from medical text
def medicaltext_to_prolog(medical_text: str) -> str:
    client = get_openai_client()

    prompt = read_prompt("kb_generator.txt").format(
        medical_text=medical_text
    )

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate only valid SWI-Prolog code."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()


def userqa_to_prolog_query(question: str, prolog_code: str) -> str:
    client = get_openai_client()

    prompt = read_prompt("qa_to_query.txt").format(
        question=question,
        prolog_code=prolog_code
    )


    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    query = response.output_text.strip()
    query = query.replace("?-", "").strip()

    if query.endswith("."):
        query = query[:-1]

    return query

def prolog_result_to_final_answer(
    question: str,
    query: str,
    result
) -> str:
    client = get_openai_client()

    prompt = read_prompt("response_generator.txt").format(
        question=question,
        query=query,
        result=result
    )

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text.strip()


if __name__ == "__main__":
    # generiert prolog query von medical text (jedes mal überschrieben)
    #generate_diabetes_diagnosis_pl()

    prolog_code = Path("test_diabetes_diagnosis.pl").read_text(encoding="utf-8")

    janus.consult("test_diabetes_diagnosis.pl")

    user_qa = input("Ask a medical question: ")

    query = userqa_to_prolog_query(
        question = user_qa,
        prolog_code = prolog_code
    )

    result = janus.query_once(query)

    final_answer = prolog_result_to_final_answer(
        question = user_qa,
        query = query,
        result = result
    )

    # TODO: Automatically generate `query` from a user question using an LLM
    #query = "diagnose(Disease)"
    #result = janus.query_once(query)

    # TODO: Automatically translate the Prolog response to a final answer using an LLM
    print("Final answer: ")
    print(final_answer)