from modalities.validation import parse_float

def handle_numeric(question: str) -> float:
    while True:
        answer = input(f"{question} Enter numeric value: ").strip()

        value = parse_float(answer)
        if value is not None:
            return value

        print("Please enter a numeric value, for example 126, 6.5 or 11,1.")