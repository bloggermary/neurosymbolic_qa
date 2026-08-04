from modalities.validation import ModalityValidator

class MedicationHandler:
    """
    Handles multiple-choice input e.g. for medication, with "other" follow-up.
    """

    def handle(self, question: str, options: list[str]) -> list[str]:
        
        valid_options = [option.lower() for option in options]

        while True:
            print(f"\n{question}") # e.g. Are you taking any of the following medications?

            for option in options:
                print(f"-{option}")
            
            print("- other")
            print("- none")

            answer = input(f"\nPlease enter one or more options or 'none' (comma-separated): ").strip().lower() # e.g. options = medication

            selected = ModalityValidator.parse_category_multiple(
                answer,
                options
            )

            if selected is None:
                print("Please choose only from the listed options.")
                continue

            result = []

            for item in selected:

                # normal options
                if item in valid_options:
                    result.append(item) 

                # OTHER - follow up question
                elif item == "other":
                    other = input(f"Please specify the other e.g. medication(s) (comma-separated): ").strip().lower()

                    if other:
                        result.extend([m.strip() for m in other.split(",") if m.strip()])

                # NONE - return immediately
                elif item == "none":
                    return []
                
                else:
                    print(f"'{item}' is not a valid option.")
                    break
            
            else:
                return result
