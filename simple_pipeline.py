import re

# read text file & build knowledge base

def normalize(text):
    return text.lower().strip().replace(".", "")

def extract_knowledge(file_path):
    facts = []

    with open(file_path, "r") as f:
        for line in f:
            line = normalize(line)

            if "causes" not in line:
                continue

            disease, symptoms = line.split("causes")

            disease = disease.strip().replace(" ", "_")
            symptoms = symptoms.replace(",", " and ").split("and")

            facts.append(f"disease({disease}).")

            for s in symptoms:
                symptom = s.strip().replace(" ", "_")
                facts.append(f"symptom({disease}, {symptom}).")

    return facts


# save prolog knowledge base for future references

def save_prolog(facts, filename="medical_kb.pl"):
    with open(filename, "w") as f:
        for fact in facts:
            f.write(fact + "\n")


# convert natural language question into prolog query

def question_to_query(question):
    question = question.lower()

    # first: symptoms of a disease
    match = re.match(r"what symptoms does (.+) have", question)
    if match:
        disease = match.group(1).strip().replace(" ", "_")
        return f"symptom({disease}, X)"

    # second: disease from symptom
    match = re.match(r"which disease causes (.+)", question)
    if match:
        symptom = match.group(1).strip().replace(" ", "_")
        return f"symptom(X, {symptom})"

    return None


# execute prolog simulated with python

def run_query(facts, query):

    predicate = query.split("(")[0]
    args = query.split("(")[1].replace(")", "").split(",")

    results = set()

    for fact in facts:

        if fact.startswith(predicate):

            inside = fact[len(predicate)+1:-2]
            a, b = [x.strip() for x in inside.split(",")]  # FIX: strip spaces

            # Query: symptom(X, fever)
            if args[1].strip() == b:
                results.add(a)

            # Query: symptom(flu, X)
            if args[0].strip() == a:
                results.add(b)

    return list(results)


# respond in natural language

def answer(question, results):

    if "symptoms" in question:
        return "The symptoms are: " + ", ".join(results)

    if "disease" in question:
        return "Possible diseases are: " + ", ".join(results)

    return "No answer found"


# full pipeline with all subtasks
def main():

    # build knowledge base from file
    facts = extract_knowledge("simple_medical.txt")
    save_prolog(facts)

    print("\n=== Medical QA System Ready ===")
    print("Type your question (or type 'exit' to stop)\n")

    while True:

        question = input("Question: ")

        if question.lower() == "exit":
            print("Goodbye!")
            break

        # convert natural language to Prolog
        query = question_to_query(question)

        if query is None:
            print("I could not understand the question.\n")
            continue

        # execute query
        results = run_query(facts, query)

        # output natural language answer
        response = answer(question, results)

        print("Answer:", response)
        print()



if __name__ == "__main__":
    main()