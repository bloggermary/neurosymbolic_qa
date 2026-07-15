"""
Theme configuration for the Streamlit interface.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """
    Global color palette.

    Feel free to adjust later.
    """

    primary: str = "#2563eb"

    secondary: str = "#0f172a"

    background: str = "#f8fafc"

    assistant_message: str = "#ffffff"

    user_message: str = "#2563eb"

    border: str = "#dbe4ee"

    text_dark: str = "#111827"

    text_light: str = "#ffffff"

    radius: int = 14

    spacing: int = 18


theme = Theme()