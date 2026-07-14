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
    def normalize_string(value: str):
        if not isinstance(value, str):
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

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