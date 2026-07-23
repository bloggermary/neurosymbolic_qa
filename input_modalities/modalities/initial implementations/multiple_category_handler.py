from modalities.validation import ModalityValidator

class MultipleCategoryHandler:    # MultipleChoiceHandler
    """
    Handles multiple-choice user input (e.g. for medication, medical history, symptoms).
    """

    def handle(self, question: str, categories: list[str]) -> list[str]:

        display_categories = categories.copy() 
        
        if "none" not in [c.lower() for c in display_categories]:
            display_categories.append("none")
        
        print(f"{question}")
        for category in display_categories:
            print(f"- {category}")
        
        print()

        while True:
            
            answer = input("\nPlease enter one or more options or 'none' (comma-separated): ")

            result, error = ModalityValidator.parse_multiple_categories(
                answer,
                categories
            )

            if result is not None:
                return result
            
            print(f"\n{error}\n")
