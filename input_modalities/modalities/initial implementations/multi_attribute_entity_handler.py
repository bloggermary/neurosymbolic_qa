from modalities.validation import ModalityValidator

class MultiAttributeEntityHandler:
    """
    Handles input for a single entity with multiple attributes. 
    Example: medication, allergy, diagnosis
    """

    def handle(self, question: str, entity: str, fields: list[tuple[str, str, str]]) -> dict:
        """
        schema = {
            "entity": str,
            "fields": [(key, prompt, type)]
        }
        """
        
        print(f"\n{question}\n")

        result = {}

        for key, prompt, field_type in fields:
            
            value = self._ask_field(prompt, field_type)

            result[key] = value

        return {
            "entity": entity,
            "data": result
        }
    
    def _ask_field(self, prompt: str, field_type: str):

        while True:
            
            answer = input(f"{prompt}: ").strip()

            if answer.lower() == "none" or answer == "":
                return None
            
            value = self._validate(field_type, answer)

            if value is not None:
                return value
            
            print("Invalid input. Please try again.")

    
    def _validate(self, field_type: str, value: str):

        if field_type == "string":
            return ModalityValidator.is_string(value)
        
        if field_type == "int":
            return ModalityValidator.is_numeric(value)
        
        if field_type == "float":
            return ModalityValidator.parse_float(value)
        
        if field_type == "bool":
            return ModalityValidator.normalize_yes_no(value)
        
        if field_type == "category":
            return value.lower()
        
        return value 
