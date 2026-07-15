"""
Custom CSS used throughout the application.
"""

from ui.styles.theme import theme


def load_css() -> str:
    """
    Returns custom CSS for the application.
    """

    return f"""
<style>

/* Hide Streamlit default menu */

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

header {{
    visibility: hidden;
}}


/* Main page */

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}}


/* Chat bubbles */

.user-message {{

    background-color: {theme.user_message};

    color: white;

    border-radius: {theme.radius}px;

    padding: 14px;

    margin-bottom: 12px;

    margin-left: 15%;

}}

.assistant-message {{

    background-color: {theme.assistant_message};

    border: 1px solid {theme.border};

    border-radius: {theme.radius}px;

    padding: 14px;

    margin-bottom: 12px;

    margin-right: 15%;

}}


/* Sidebar */

section[data-testid="stSidebar"] {{

    background-color: white;

    border-right: 1px solid {theme.border};

}}


/* Expander */

.streamlit-expanderHeader {{

    font-weight: 600;

}}

</style>
"""