


class MultiStructuredInputHandler:

    def handle(self, question: str, mode: str):

        self.question = question 

        print(f"\n{question}")

        if mode == "sequence":
            return self._handle_sequence()
        
        elif mode == "ranking":
            return self._handle_ranking()
        
        elif mode == "grouping":
            return self._handle_grouping()
        
        
        else:
            raise ValueError(f"Unknown mode: {mode}") 
        


    def handle_sequence(self):

        print("Enter events in chronological order.") 
        print("Type 'done' when finished.\n")

        result = []

        while True:
            answer = input("> ").strip()

            if answer.lower() == "done":
                break

            result.append(answer)
        
        return result 
    

    def handle_ranking(self):

        print("Enter the items from most important to least important.")
        print("Type 'done' when finished.\n")

        result = []

        rank = 1

        while True:
            answer = input(f"{rank}. ").strip()

            if answer.lower() == "done":
                break

            result.append({
                "rank": rank,
                "value": answer
            })

            rank += 1
        
        return result
    

    def handle_grouping(self):

        print("Type 'done' when finished.\n")

        result = {}

        while True:
            group = input("Group: ").strip()
            if group.lower() == "done":
                break

            items = []

            # rule: empty group still exists
            print(f"{group}:")

            while True:
                item = input().strip()

                if item.lower() == "done":
                    break

                # allow empty meaning "none"
                if item.lower() == "none":
                    continue

                items.append(item)

            result[group.lower()] = items

        return result
