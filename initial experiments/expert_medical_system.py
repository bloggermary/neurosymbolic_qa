from pyswip import Prolog


# normalize text
def normalize(text):
    return text.lower().strip().replace(".", "")


# extract facts from text file
def extract_facts_from_file(filename):
    facts = []

    with open(filename, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = normalize(line)

        if "causes" in line:
            disease, symptoms = line.split("causes", 1)

        elif "is characterized by" in line:
            disease, symptoms = line.split("is characterized by", 1)

        elif "leads to" in line:
            disease, symptoms = line.split("leads to", 1)

        else:
            continue

        disease = disease.strip().replace(" ", "_")
        symptoms = symptoms.split(",")

        facts.append(f"disease({disease}).")

        for s in symptoms:
            s = s.strip().replace(" ", "_")
            if s:
                facts.append(f"symptom({disease}, {s}).")

    return facts


# save prolog kb
def save_kb(facts, filename="kb.pl"):
    with open(filename, "w") as f:
        for fact in facts:
            f.write(fact + "\n")


# load prolog
def load_prolog(kb_file="kb.pl"):
    prolog = Prolog()
    prolog.consult(kb_file)
    return prolog


# parse question
def parse_question(q):
    q = q.lower()

    if "symptom" in q and "of" in q:
        disease = q.split("of")[-1].strip().replace(" ", "_")
        return ("disease_to_symptom", disease)

    if "which disease" in q or "what disease" in q:
        if "cause" in q or "linked" in q:
            symptom = q.split("to")[-1].strip().replace(" ", "_")
            return ("symptom_to_disease", symptom)

    return (None, None)


# build prolog query
def build_query(mode, value):
    if mode == "disease_to_symptom":
        return f"symptom({value}, X)"

    if mode == "symptom_to_disease":
        return f"symptom(X, {value})"

    return None


# run query
def run_query(prolog, query):
    if not query:
        return []

    try:
        return list(prolog.query(query))
    except:
        return []


# format answer
def format_answer(results, mode):
    if not results:
        return "no medical knowledge found"

    if mode == "disease_to_symptom":
        symptoms = [r["X"] for r in results]
        return "symptoms: " + ", ".join(symptoms)

    if mode == "symptom_to_disease":
        diseases = [r["X"] for r in results]
        return "possible diseases: " + ", ".join(diseases)

    return str(results)


# get all symptoms from kb
def get_all_symptoms(prolog):
    result = list(prolog.query("symptom(_, X)"))
    return sorted(set([r["X"] for r in result]))


# follow up engine
class FollowUpEngine:

    def __init__(self, prolog):
        self.prolog = prolog
        self.answers = {}

    def next_question(self):
        symptoms = get_all_symptoms(self.prolog)

        for s in symptoms:
            if s not in self.answers:
                return f"do you experience {s.replace('_', ' ')}? (yes/no)", s

        return None, None

    def update(self, symptom, answer):
        self.answers[symptom] = answer.lower()


# main system
def main():

    # read input file
    facts = extract_facts_from_file("extended_medical.txt")

    # build kb
    save_kb(facts)

    # load prolog
    prolog = load_prolog()

    followup = FollowUpEngine(prolog)

    print("medical expert system ready\n")

    while True:

        q = input("question: ")

        if q.lower() == "exit":
            break

        mode, value = parse_question(q)
        query = build_query(mode, value)

        results = run_query(prolog, query)

        print(format_answer(results, mode))

        fq, symptom = followup.next_question()

        if fq:
            ans = input(fq + "\n> ")
            followup.update(symptom, ans)


if __name__ == "__main__":
    main()