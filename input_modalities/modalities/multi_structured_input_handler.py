


class MultiStructuredInputHandler:

    def handle(self, question: str, mode: str):

        print(f"\n{question}")

        if mode == "sequence":
            return self._handle_sequence()
        
        elif mode == "ranking":
            return self._handle_ranking()
        
        elif mode == "graph":
            return self._handle_graph()
        
        elif mode == "entity":
            return self._handle_entity()
        
        else:
            raise ValueError(f"Unknown mode: {mode}") 
        


    def handle_sequence(self):

        print(f"{question}\nEnter events in chronological order.\nType 'done' when finished.\n")

        result = []

        while True:
            answer = input("> ").strip()

            if answer.lower() == "done":
                break

            result.append(answer)
        
        return result 
    

    def handle_ranking(self):

        print(f"{question}\nEnter the items from most important to least important.\nType 'done' when finished.\n")

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
    

    def handle_graph(self):

        print(f"{question}\nEnter relationships.\nFormat: cause -> effect\nType 'done' when finished.\n")

        result = []

        while True:
            answer = input("> ").strip()

            if answer.lower() == "done":
                break

            if "->" not in answer:
                print(f"Please use the format: 'cause -> effect'.")
                continue

            cause, effect = answer.split("->", 1)

            result.append[{
                "from": cause.strip()
                "to": effect.strip()
            }]

        return result
    

    def handle_entity(self):

        print(f"{question}\nEnter the entity and its attributes.\nType 'done' when finished.\n")

        result = {}

        # Entity name
        while True:
            entity = input(f"Name: ").strip()

            if entity == "":
                print(f"Please enter an entity.")
                continue

            result["entity"] = entity 
            break

        # Entity attributes:
        for attribute in attributes:
            value = input(f"{attribute}: ").strip()
            result[attribute] = value
        
        return result 





    