import janus_swi as janus
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

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
    load_dotenv()
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    prompt = f"""
Generate a SWI-Prolog medical diagnosis program from this text.

Requirements:
- Use:
  :- use_module(library(janus)).

- Define:
  ask(Question) :-
      py_call(diabetes_diagnosis:ask(Question), yes).

- The program must use only yes/no questions.
- Create diabetes diagnosis rules.
- Create diagnose/1.
- Return ONLY Prolog code.
- No markdown.
- Ask ALL diagnostic questions before making a diagnosis.
- Never stop after the first positive answer.
- First collect all answers.
- Do NOT structure the diagnosis as:
    (condition1 ; condition2 ; condition3), !
  because this skips remaining questions.
- Store intermediate answers in predicates or variables if necessary.
- The generated program should support future extension with follow-up questions.

#medical_diabetes.txt LLM
Medical text:
{medical_text} 
"""
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

    prompt = f"""
You are a Prolog query generator. From natural language to Prolog query.

Given this Prolog knowledge base:

{prolog_code}

Convert the user question into exactly one valid Prolog query.

Rules:
- Return only the Prolog query.
- Do not explain.
- Do not use ?-.
- Do not add markdown.
- The user can only ask yes/no medical questions.
- Return only a predicate that already exists in the Prolog knowledge base.
- Do not invent new predicates.
- Do not use ?-.
- Do not add markdown.
- If the question asks whether diabetes is present in general, use diagnose(diabetes).
- If the question asks about HbA1c, use hba1c.
- If the question asks about random plasma glucose / Gelegenheits-Plasmaglukose, use random_plasma_glucose.
- If the question asks about fasting plasma glucose / Nüchtern-Plasmaglukose, use fasting_plasma_glucose.
- If the question asks about oral glucose tolerance test / OGTT, use ogtt_2h.
- If no matching predicate exists, return fail.

User question:
{question}
"""

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

    prompt = f"""
You are a medical QA assistant.

User question:
{question}

Executed Prolog query:
{query}

Raw Prolog result:
{result}

Write a short final answer for the user.

Rules:
- Answer in natural language.
- Do not print raw Python dictionaries.
- Say that the answer is based only on the generated Prolog knowledge base.
- Do not claim this is a real medical diagnosis.
- If the result is false, None, or empty, say that no matching diagnosis was found.
"""

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