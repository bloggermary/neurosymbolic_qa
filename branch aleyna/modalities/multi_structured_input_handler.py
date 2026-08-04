from modalities.validation import ModalityValidator

class MultiStructuredInputHandler:
    """
    Handles structured multi-input data.

    Supported modes:
    - sequence
    - ranking
    - grouping
    """

    def handle(self, question: str, mode: str, groups: list[str] | None = None):

        print(f"\n{question}\n")

        if mode == "sequence":
            return self._handle_sequence()
        
        elif mode == "ranking":
            return self._handle_ranking()
        
        elif mode == "grouping":
            return self._handle_grouping(groups)
                
        else:
            raise ValueError(f"Unknown mode: {mode}") 
        


    def _handle_sequence(self) -> list[str]:

        print("Enter items in chronological order.") 
        print("Type 'done' when finished.\n")

        result = []

        index = 1

        while True:
            
            answer = input(f"{index}. ").strip()

            if answer.lower() == "done":
                break

            value = ModalityValidator.normalize_string(answer)

            if value is None:
                print("Please enter a non-empty value.")
                continue

            result.append(value)

            index += 1
        
        return result
    

    def _handle_ranking(self) -> list[dict[str, object]]:

        print(f"Rank the items from most important to least important.")
        print("Type 'done' when finished.\n")

        result = []
        rank = 1

        while True:

            answer = input(f"{rank}. ").strip()

            if answer.lower() == "done":
                break

            value = ModalityValidator.normalize_string(answer)

            if value is None:
                print("Please enter a non-empty value.")
                continue

            result.append({
                "rank": rank,
                "value": value
            })

            rank += 1
        
        return result
    

    def _handle_grouping(self, groups: list[str]) -> dict[str, list[str]]:

        if not groups:
            raise ValueError("Grouping mode requires a list of groups.")

        print("Type 'done' when finished.\n")
        print("Enter 'none' if there are no items for a group.\n") 

        result = {}

        for group in groups:
            print(f"{group}: ")
            items = []

            while True:

                answer = input().strip()

                if answer.lower() == "done":
                    break

                if answer.lower() == "none":
                    items = []
                    break

                value = ModalityValidator.normalize_string(answer)

                if value is None:
                    print("Please enter a non-empty value.")
                    continue

                items.append(value)

            result[group] = items
                 
            print()

        return result
