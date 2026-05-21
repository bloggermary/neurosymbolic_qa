import re

# normalzie text

def normalize(text):
    return text.lower().strip().replace(".", "")


# extract knowledge from text into facts


def extract_knowledge(file_path):

    facts = []

    patterns = [
        "causes",
        "is associated with",
        "often presents with",
        "typically leads to",
        "is characterized by",
        "is linked to"
    ]

    with open(file_path, "r") as f:
        for line in f:

            line = line.lower().strip().replace(".", "")

            matched = False

            for p in patterns:
                if p in line:
                    disease, symptoms = line.split(p, 1)
                    matched = True
                    break

            if not matched:
                continue

            disease = disease.strip().replace(" ", "_")

            symptoms = symptoms.replace(",", " and ").split("and")

            facts.append(f"disease({disease}).")

            for s in symptoms:
                symptom = s.strip().replace(" ", "_")

                if symptom:
                    facts.append(f"symptom({disease}, {symptom}).")

    return facts

# build index

def build_index(facts):

    disease_to_symptoms = {}
    symptom_to_diseases = {}

    for f in facts:

        f = f.replace(".", "")
        pred, args = f.split("(")
        args = args.replace(")", "").split(",")

        # ❗ SAFETY CHECK (FIX)
        if len(args) != 2:
            continue

        a = args[0].strip()
        b = args[1].strip()

        if pred == "symptom":
            disease_to_symptoms.setdefault(a, []).append(b)
            symptom_to_diseases.setdefault(b, []).append(a)

    return disease_to_symptoms, symptom_to_diseases

# convert from natural language into prolog query

def parse_question(question):

    q = question.lower().strip()

    # convert from disease to symptom(s)
    if ("symptoms" in q) and ("malaria" in q or "of" in q):
        disease = q.split("of")[-1].strip().replace(" ", "_")
        return ("disease_to_symptoms", disease)

    if "what symptoms" in q:
        if "of" in q:
            disease = q.split("of")[-1].strip().replace(" ", "_")
            return ("disease_to_symptoms", disease)
        if "linked to" in q:
            disease = q.split("linked to")[-1].strip().replace(" ", "_")
            return ("disease_to_symptoms", disease)

    # convert from symptom to disease(s)
    if ("which disease" in q or "which diseases" in q):

        if "cause" in q:
            symptom = q.split("cause")[-1].strip().replace(" ", "_")
            return ("symptom_to_diseases", symptom)

        if "linked to" in q:
            symptom = q.split("linked to")[-1].strip().replace(" ", "_")
            return ("symptom_to_diseases", symptom)

    return (None, None)

# execute query through a structured lookup

def run_query(parsed, d2s, s2d):

    mode, value = parsed

    if mode == "disease_to_symptoms":
        return d2s.get(value, [])

    if mode == "symptom_to_diseases":
        return s2d.get(value, [])

    return []


# respond in natural language

def format_answer(question, results):

    if not results:
        return "No medical knowledge found for this query."

    if "symptoms" in question:
        return "The symptoms are: " + ", ".join(results)

    if "disease" in question:
        return "Possible diseases are: " + ", ".join(results)

    return ", ".join(results)


# main pipeline with all subtasks
def main():

    facts = extract_knowledge("extended_medical.txt")

    print("=== SAMPLE FACTS ===")
    print(facts[:20])

    disease_index, symptom_index = build_index(facts)

    print("\n=== MEDICAL EXPERT SYSTEM READY ===")
    print("Type 'exit' to stop\n")

    while True:

        question = input("Question: ")

        if question.lower() == "exit":
            break

        parsed = parse_question(question)

        results = run_query(parsed, disease_index, symptom_index)

        print("Answer:", format_answer(question, results))
        print()


if __name__ == "__main__":
    main()