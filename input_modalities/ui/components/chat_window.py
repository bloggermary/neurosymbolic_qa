"""
Conversation renderer.
"""

from __future__ import annotations

from services.session_service import session
from ui.components.message import render_message


def render_chat_window() -> None:
    """
    Display the complete conversation.
    """

    for message in session.get_messages():
        render_message(message)