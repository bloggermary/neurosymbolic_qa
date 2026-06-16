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
    def parse_float(value: str) -> Optional[float]:
        value = value.strip().replace(",", ".")

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def normalize_string(value: str) -> str:
        return value.strip().strip("'").strip('"')