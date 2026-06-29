from modalities.validation import ModalityValidator

class MultiAttributeEntityHandler:
    """
    Handles input for a single entity with multiple attributes. 
    Example: medication, allergy, diagnosis
    """

    def handle(self, schema: dict) -> dict:
        """
        schema = {
            "entity": str,
            "fields": [(key, prompt, type)]
        }
        """
        
        print(f"\nDescribe your {schema['entity']}.\n")

        result = {}

        for field in schema["fields"]:

            key, prompt, field_type = field

            value = self._ask_field(key, prompt, field_type)

            result[key] = value

        return {
            "entity": schema["entity"],
            "data": result
        }
    
    def _ask_field(self, prompt: str, field_type: str):

        while True:
            answer = input(f"{prompt}: ").strip()

            if answer.lower() in {"none", ""}:
                return None
            
            validated = self._validate(field_type, answer)

            if validated is not None:
                return validated
            
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
            





           # answer = input(f"{attribute}: ").strip()

            # allow empty input 
           # if answer.lower() == "none" or answer == "":
          #      result[attribute] = None
            #else: 
             #   result[attribute] = answer

        #return result 