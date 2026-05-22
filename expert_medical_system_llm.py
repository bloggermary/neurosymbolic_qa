from openai import OpenAI
from pyswip import Prolog
import json


client = OpenAI()


# read medical text
def read_text_file(filename):
    with open(filename, "r") as f:
        return f.read()


# generate prolog knowledge base using llm
def generate_prolog_kb(text):

    prompt = f"""
Convert the following medical text into valid Prolog facts.

Rules:
- Output ONLY Prolog code
- Use lowercase
- Replace spaces with underscores
- End every fact with a period

Use predicates such as:
disease/1
symptom/2
treatment/2
risk_factor/2

Example:
disease(diabetes).
symptom(diabetes, fatigue).

Medical text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate only valid Prolog code."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


# save prolog kb
def save_kb(prolog_code, filename="kb.pl"):
    with open(filename, "w") as f:
        f.write(prolog_code)


# load prolog
def load_prolog(kb_file="kb.pl"):
    prolog = Prolog()
    prolog.consult(kb_file)
    return prolog


# generate prolog query using llm
def generate_prolog_query(question, kb_text):

    prompt = f"""
You are given a Prolog knowledge base and a user question.

Generate ONE valid Prolog query.

Rules:
- Output ONLY the query
- Do not explain anything
- Use variables like X if needed
- Do not include '?-'

Knowledge base:
{kb_text}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate only valid Prolog queries."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


# execute prolog query
def run_query(prolog, query):

    try:
        return list(prolog.query(query))
    except Exception as e:
        return [{"error": str(e)}]


# translate result using llm
def translate_result(question, result):

    prompt = f"""
A Prolog system answered the following medical question.

Question:
{question}

Prolog result:
{json.dumps(result)}

Explain the result naturally and clearly for the user.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You explain Prolog medical query results."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# get all symptoms from kb
def get_all_symptoms(prolog):

    try:
        result = list(prolog.query("symptom(_, X)"))
        return sorted(set([r["X"] for r in result]))
    except:
        return []


# follow up engine
class FollowUpEngine:

    def __init__(self, prolog):
        self.prolog = prolog
        self.answers = {}

    def next_question(self):

        symptoms = get_all_symptoms(self.prolog)

        for symptom in symptoms:

            if symptom not in self.answers:
                return (
                    f"do you experience {symptom.replace('_', ' ')}? (yes/no)",
                    symptom,
                    "boolean"
                )

        return None, None, None

    def update(self, symptom, answer):
        self.answers[symptom] = answer.lower()


# main system
def main():

    print("medical neurosymbolic qa system\n")

    # read medical document
    text = read_text_file("extended_medical.txt")

    # llm generates prolog kb
    print("generating prolog knowledge base...\n")

    kb_code = generate_prolog_kb(text)

    print("generated knowledge base:\n")
    print(kb_code)
    print()

    # save kb
    save_kb(kb_code)

    # load prolog
    prolog = load_prolog()

    # initialize follow up system
    followup = FollowUpEngine(prolog)

    while True:

        question = input("question: ")

        if question.lower() == "exit":
            break

        # llm generates prolog query
        query = generate_prolog_query(question, kb_code)

        print("\nprolog query:")
        print(query)

        # execute query
        result = run_query(prolog, query)

        print("\nraw prolog result:")
        print(result)

        # llm translates result
        final_answer = translate_result(question, result)

        print("\nanswer:")
        print(final_answer)

        # follow up question
        fq, symptom, qtype = followup.next_question()

        if fq:

            user_answer = input(f"\nfollow-up ({qtype}): {fq}\n> ")

            followup.update(symptom, user_answer)

        print()


if __name__ == "__main__":
    main()
