# prolog query validation
def validate_query(query: str) -> str:
    query = query.strip()

    if query.startswith("?-"):
        query = query[2:].strip()

    if query.endswith("."):
        query = query[:-1].strip()

    if not query:
        raise ValueError("Generated query is empty.")

    return query

def normalize_text(value: str) -> str:
    """
    Normalizes simple user input.
    """
    return value.strip().lower()


def normalize_yes_no(value: str):
    value = value.strip().lower()

    if value in {"yes", "y", "ja", "j"}:
        return "yes"

    if value in {"no", "n", "nein"}:
        return "no"

    return None


def parse_float(value: str):
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def normalize_text(value: str):
    return value.strip().lower()
