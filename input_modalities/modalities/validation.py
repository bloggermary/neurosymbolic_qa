# modalities/validation.py

from typing import Any, Optional


class ModalityValidator:
    """
    Validates and normalizes user input for different modalities.
    """

    @staticmethod
    def is_boolean(value: Any) -> bool:
        return isinstance(value, bool)

    @staticmethod
    def is_numeric(value: Any) -> bool:
        return isinstance(value, (int, float))

    @staticmethod
    def is_string(value: Any) -> bool:
        return isinstance(value, str)
    
    @staticmethod
    def is_scale(value: Any) -> bool:
        return isinstance(value, int)
    
    @staticmethod
    def parse_category_multiple(answer: str, options: list[str]):
        """
        Validates multiple categorical inputs.
        Returns a list of valid selections or None.
        """

        try: 
            selected = [
                item.strip().lower()
                for item in answer.split(",")
                if item.strip
            ] 
        except AttributeError:
            return None
        
        valid_options = [option.lower() for option in options]

        valid = []

        for item in selected:
            if item in valid_options or item in ["other", "none"]:
                valid.append(item)
            else:
                return None
            
        return valid
    

    @staticmethod
    def normalize_yes_no(value: str) -> Optional[bool]:
        value = value.strip().lower()

        if value in {"yes", "ja", "true", "1"}:
            return True

        if value in {"no", "nein", "false", "0"}:
            return False

        return None

    @staticmethod
    def parse_float(value: str) -> Optional[float]:
        value = value.strip().replace(",", ".")

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def normalize_string(value: str) -> str:
        return value.strip().strip("'").strip('"')