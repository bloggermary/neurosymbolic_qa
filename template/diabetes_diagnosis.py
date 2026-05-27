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


def generate_diabetes_diagnosis_pl() -> None:
    medical_text = Path("medical_diabetes.txt").read_text(encoding="utf-8")

    prolog_code = medicaltext_to_prolog(medical_text)

# save prolog code in diabetes_diagnosis.pl
    Path("test_diabetes_diagnosis.pl").write_text(
        prolog_code,
        encoding="utf-8"
    )



if __name__ == "__main__":
    #generate_diabetes_diagnosis_pl()
    janus.consult("test_diabetes_diagnosis.pl")

    # TODO: Automatically generate `query` from a user question using an LLM
    query = "diagnose(Disease)"
    result = janus.query_once(query)

    # TODO: Automatically translate the Prolog response to a final answer using an LLM
    print(result)