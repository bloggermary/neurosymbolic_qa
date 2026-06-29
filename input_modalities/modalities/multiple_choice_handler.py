from modalities.validation import ModalityValidator

class MultipleChoiceHandler:
    """
    Generic handler for any multiple-choice input (e.g. medication, medical history, symptoms) with optional "other" follow-up.
    """

    def handle(self, question: str, options: list[str], allow_other: bool = True) -> list[str]:
        
        valid_options = [option.lower() for option in options]

        while True:
            print(f"\n{question}") # e.g. Are you taking any of the following medications?

            for option in options:
                print(f"-{option}")
            
            
            print("- none")

            answer = input(f"\nPlease enter one or more options or 'none' (comma-separated): ").strip().lower() # e.g. options = medication

            selected = ModalityValidator.parse_category_multiple(
                answer,
                options
            )

            if selected is None:
                print("Invalid input. Please choose only from the listed options.")
                continue

            result = []

            for item in selected:
                
                # NONE - return immediately
                if item == "none":
                    return []
                
                # normal option(s)
                if item in valid_options:
                    result.append(item) 

               
                        
            else:
                return result
