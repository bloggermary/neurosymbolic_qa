from modalities.validation import ModalityValidator

class FrequencyHandler:
    """
    Handles frequency-based inputs (e.g. symptoms occurence).
    """

    DEFAULT_OPTIONS = [
        "never"
        "rarely"
        "sometimes"
        "often"
        "daily"
    ]

    def handle(self, question: str, options: list[str] = None) -> str:
        if options is None:
            options = self.DEFAULT_OPTIONS

        options_lower = [o.lower() for o in options]

        while True:
            answer = input(f"{question} ({'/'.join(options)}): ").strip().lower()

            if answer in options_lower:
                return answer
            
            print(f"Please choose one of: {', '.join(options)}")