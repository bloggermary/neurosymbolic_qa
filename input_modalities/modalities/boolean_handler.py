from modalities.validation import normalize_yes_no

def handle_boolean(question: str) -> bool:
    while True:
        answer = input(f"{question} [yes/no]: ").strip().lower()

        normalized = normalize_yes_no(answer)

        if normalized is not None:
            return normalized

        print("Please answer with yes or no.")