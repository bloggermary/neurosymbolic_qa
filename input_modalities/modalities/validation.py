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
    def normalize_yes_no(value: str) -> Optional[bool]:
        value = value.strip().lower()

        if value in {"yes", "ja", "true", "1"}:
            return True

        if value in {"no", "nein", "false", "0"}:
            return False

        return None

    @staticmethod
    def parse_float(value: str) -> float:
        value = value.strip()
        value = value.replace(",", ".")

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def normalize_string(value: str) -> str:
        return value.strip().strip("'").strip('"')
    
    @staticmethod
    def parse_int_range(answer: str, start: int, stop: int):
        try:
            value = int(answer.strip())
        except (ValueError, AttributeError):
            return None
        
        if start <= value <= stop:
            return value

        return None
    
    @staticmethod
    def parse_int_duration(value: str) -> int:
        try:
            number = int(value.strip())
        except ValueError:
            return None

        if number >= 0:
            return number

        return None

    @staticmethod
    def parse_multiple_categories(answer: str, categories: list[str]) -> tuple[list[str] | None, str | None]:
        """
        Parses and validates a comma-separated list of categories.
        
        - Only predefined categories are allowed.
        - "none" is always a valid option.
        - "none" cannot be combined with other options.
        
        Returns:
            (result, None) if valid
            (None, error_message) otherwise
        """

        categories = [c.strip().lower() for c in categories]

        if "none" not in categories:
            categories.append("none")
         
        selected = [
            item.strip().lower()
            for item in answer.split(",")
            if item.strip
        ] 
        
        if not selected:
            return None, "Please select at least one option."
        
        invalid = [item for item in selected if item not in categories]

        # invalid options
        if invalid:
            return(
                None,
                f"Invalid option(S): {', '.join(invalid)}.\n"
                "Please choose only from the listed options."
                )
        
        # "none" cannot be combined
        if "none" in selected and len(selected) > 1:
            return(
                None,
                "'none' cannot be combined with other options."
            )
        
        return selected, None
