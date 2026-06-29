


class MultiAttributeEntityHandler:
    """
    Handles input for a single entity with multiple attributes. 
    Example: medication, allergy, diagnosis
    """

    def handle(self, question: str, attributes: list[str]) -> dict:

        print(f"\n{question}")

        result = {}

        for attribute in attributes:

            answer = input(f"{attribute}: ").strip()

            # allow empty input 
            if answer.lower() == "none" or answer == "":
                result[attribute] = None
            else: 
                result[attribute] = answer

        return result 