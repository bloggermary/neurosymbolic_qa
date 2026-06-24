from modalities.validation import ModalityValidator

class MultipleChoiceFollowUpHandler:
    """
    Generic handler for: 
    - multi-selection questions
    - follow-up question per selected item
    """

    def handle(self, question: str, options: list[str], follow_) -> dict:

        valid_options = [option.lower() for option in options]

        while True:
            print(f"\n{question}")

            for option in options:
                print(f"-{option}")
            
            print("- other")
            print("- none")

            answer = input(f"\nPlease enter one or more conditions or 'none' (comma-separated): ").strip().lower()

            if not answer:
                print(f"Please choose only from the listed options.")
                continue

            selected = ModalityValidator.parse_category_multiple(
                answer,
                options
            )

            result = {}

            for item in selected:

                # normal options
                if item in valid_options:
                    family_member = input(f"Who in your family has {item}? " "(e.g. mother, father, sibling): ").strip().lower()
                    result [item] = family_member

                # OTHER - follow up question
                elif item == "other":
                    other = input(f"Please specify the other condition(s) (comma-separated): ").strip().lower()

                    for condition in other.split(","):
                        condition = condition.strip()

                        if not condition:
                            continue

                        family_member = input(f"Who in your family has {condition}? ""(e.g. mother, father, sibling): ").strip().lower()
                        result[condition] = family_member

                # NONE - return immediately
                elif item == "none":
                    return []
                
                else:
                    print(f"'{item}' is not a valid option.")
                    break
            
            else:
                return result
