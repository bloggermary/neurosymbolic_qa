def handle_string(question: str) -> str:
    while True:
        answer = input(f"{question} Enter text value: ").strip().lower()

        if answer:
            return answer

        print("Please enter a non-empty answer.")