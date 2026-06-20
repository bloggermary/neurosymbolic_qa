import janus_swi as janus


# The user interaction method that is being called from Prolog in `diabetes_diagnosis.pl`
def ask(question: str) -> str:
    """Called from Prolog via py_call(diabetes_diagnosis:ask(Question), "yes")."""
    return input(question).strip().lower()


# Categorical variant: restricts the answer to one of `permissible_categories`.
def ask_category(question: str, permissible_categories: list[str]) -> str:
    """Called from Prolog via py_call(diabetes_diagnosis:ask_category(Question, Categories), Answer)."""
    categories = [c.strip().lower() for c in permissible_categories]
    prompt = f"{question} ({'/'.join(categories)}) "
    answer = input(prompt).strip().lower()
    if answer in categories:
        return answer
    print(f"Please answer with one of: {', '.join(categories)}")


# TODO: Automatically generate `diabetes_diagnosis.pl` from medical text using an LLM
# TODO: Make sure that the automatically generated `diabetes_diagnosis.pl` uses the `ask` method below

if __name__ == "__main__":
    janus.consult("diabetes_diagnosis.pl")

    # TODO: Automatically generate `query` from a user question using an LLM
    query = "thirst_severity(Severity)"
    result = janus.query_once(query)

    # TODO: Automatically translate the Prolog response to a final answer using an LLM
    print(result)
