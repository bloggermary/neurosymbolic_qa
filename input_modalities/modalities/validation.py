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
    def parse_int(value: str) -> Optional[int]:
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def normalize_string(value: str) -> Optional[str]:
        """
        Returns the stripped string, or None if it's empty after
        stripping (used to reject blank entries in free-text prompts).
        """

        if value is None:
            return None

        value = value.strip()

        return value if value else None

    @staticmethod
    def parse_multiple_categories(
        answer: str,
        categories: list[str],
    ) -> tuple[Optional[list[str]], Optional[str]]:
        """
        Parses a comma-separated multi-select answer against a fixed
        set of categories (plus the always-allowed "none").

        Returns (result, error) - exactly one of which is None, so
        callers can do `if result is not None: return result`.
        """

        if answer is None or not answer.strip():
            return None, "Please enter at least one option or 'none'."

        raw_choices = [c.strip() for c in answer.split(",") if c.strip()]

        if not raw_choices:
            return None, "Please enter at least one option or 'none'."

        if len(raw_choices) == 1 and raw_choices[0].lower() == "none":
            return [], None

        valid_lookup = {c.lower(): c for c in categories}

        result = []
        invalid = []

        for choice in raw_choices:

            match = valid_lookup.get(choice.lower())

            if match is None:
                invalid.append(choice)
            elif match not in result:
                result.append(match)

        if invalid:
            return None, (
                f"Invalid option(s): {', '.join(invalid)}. "
                f"Valid options are: {', '.join(categories)}, none."
            )

        return result, None