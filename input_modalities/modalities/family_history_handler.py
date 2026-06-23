from modalities.validation import ModalityValidator

class FamilyHistoryHandler:
    """
    Handles family history input using a multipl-choice interface.
    If a condition is selected, a follow-up question asks which family member is affected.
    """

    def handle(self, question: str, options list[str]) -> dict:

        while True:
            print(f"\n{question}\n")

            for i, options in enumerate(options, start=1):
                print(f"{i}) {options}")

            print(f"{len(options)+1} other")
            print(f"{len(options)+1} none")

            answer = input("\nSelect one or more options (comma-separated numbers): ").strip()

            try: 
                selections = [int(x.strip()) for x in answer.split(",")]
            except ValueError:
                print("Please enter valid numbers.")

            results = {}

            for choice in selections:

                # predefined conditions
                if 1 <= choice <= len(options):

                    condition = options[choice -1]

                    member = input(f"Who in your family has {condition}? " "(e.g. mother, father, sibling): ").strip()

                    results[condition] = member
                
                # other 
                elif choice == len(options) + 1:

                    other = input("Please specify the other condition: ").strip()

                    if other:
                        member = input(f"Who in your family has {other}? " "(e.g. mother, father, sibling): ").strip()

                        results[other] = member

                # none
                elif choice == len(options) + 2:
                    return {}
                
                else:
                    print("Invalid selection.")
                    break
            
            else:
                return results
