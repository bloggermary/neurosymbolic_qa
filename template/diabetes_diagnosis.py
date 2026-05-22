import janus_swi as janus

# The user interaction method that is being called from Prolog in `diabetes_diagnosis.pl`
def ask(question: str) -> str:
    """Called from Prolog via py_call(diabetes_diagnosis:ask(Question), "yes")."""
    return input(question).strip().lower()

# TODO: Automatically generate `diabetes_diagnosis.pl` from medical text using an LLM
# TODO: Make sure that the automatically generated `diabetes_diagnosis.pl` uses the `ask` method below

if __name__ == "__main__":
    janus.consult("diabetes_diagnosis.pl")

    # TODO: Automatically generate `query` from a user question using an LLM
    query = "diagnose"
    result = janus.query_once(query)

    # TODO: Automatically translate the Prolog response to a final answer using an LLM
    print(result)