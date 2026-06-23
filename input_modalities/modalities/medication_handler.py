from modalities.validation import ModalityValidator

class MedicationHandler:
    """
    Multiple-choice medication input with "other" follow-up.
    """

    def handle(self, question: str, options: list[str]) -> list[str]:
        options = [o.lower() for o in options]

        while True:
            print(f"\n{question}\nAre you taking any of the following medications?") 

            for i, opt in enumerate(options, start=1):
                print(f"{i}) {opt}")

            print(f"{len(options)+1} other")
            print(f"{len(options)+2} none")

            answer = input(f"\n{question}\nPlease enter one or more medications or 'none' if not taking any (comma-separated): ").strip(),lower()

            try: 
                choices = [int(x.strip()) for x in answer.split(",")]
            except ValueError:
                print(f"Please enter one of the options only.")
                continue

            result = []

            for c in choices:

                # normal options
                if 1 <= c <= len(options):
                    result.append(options[c - 1])

                # OTHER - follow up question
                elif c == len(options) + 1:
                    other = input(f"Please specify other medications (comma-separated): ").strip().lower()

                    if other:
                        result.extend([m.strip() for m in other.split(",") if m.strip()])

                # NONE - return immediately
                elif c == len(options) + 2:
                    return []
            
            return list(set(result)) 
