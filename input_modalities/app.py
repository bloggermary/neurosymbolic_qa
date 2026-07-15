"""
Application entry point.

Launch with:

    streamlit run app.py
"""

from ui.pages.chat import render_chat


def main() -> None:
    """Launch the Streamlit interface."""
    render_chat()


if __name__ == "__main__":
    main()