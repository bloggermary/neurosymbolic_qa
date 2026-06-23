from modalities.validation import ModalityValidator

class CategoryHandler:

    def handle(self,
               question: str,
               permissible_categories: list[str]) -> str:

        categories = [c.strip().lower() for c in permissible_categories]

        while True:

            prompt = f"{question} ({'/'.join(categories)}) "
            answer = input(prompt).strip().lower()
            if answer in categories:
                return answer
            print(f"Please answer with one of: {', '.join(categories)}")