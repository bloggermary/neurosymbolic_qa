"""
Session management service.

Responsible for:
- storing conversation messages
- managing Streamlit session state
- providing a clean interface for UI/backend
"""

from __future__ import annotations


from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

import streamlit as st



@dataclass
class ChatMessage:
    """
    Represents one message in a conversation.
    """

    role: str

    content: str

    timestamp: str

    reasoning: dict[str, Any]

    sources: list[dict[str, Any]]


    @staticmethod
    def create(
        role: str,
        content: str,
        reasoning: dict | None = None,
        sources: list | None = None,
    ) -> "ChatMessage":
        """
        Factory method for creating messages.
        """

        return ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
            .strftime("%H:%M"),
            reasoning=reasoning or {},
            sources=sources or [],
        )



class SessionService:
    """
    Wrapper around Streamlit session state.
    """

    MESSAGE_KEY = "chat_messages"


    def initialize(self) -> None:
        """
        Initialize session storage.
        """

        if self.MESSAGE_KEY not in st.session_state:

            st.session_state[
                self.MESSAGE_KEY
            ] = []



    def add(
        self,
        message: ChatMessage,
    ) -> None:
        """
        Store a message.
        """

        st.session_state[
            self.MESSAGE_KEY
        ].append(
            asdict(message)
        )



    def add_user(
        self,
        content: str,
    ) -> None:
        """
        Convenience method.
        """

        self.add(
            ChatMessage.create(
                role="user",
                content=content,
            )
        )



    def add_assistant(
        self,
        content: str,
        reasoning: dict | None = None,
        sources: list | None = None,
    ) -> None:
        """
        Store assistant response.
        """

        self.add(
            ChatMessage.create(
                role="assistant",
                content=content,
                reasoning=reasoning,
                sources=sources,
            )
        )



    def get_messages(
        self,
    ) -> list[dict]:
        """
        Return conversation history.
        """

        return st.session_state.get(
            self.MESSAGE_KEY,
            [],
        )



    def clear(self) -> None:
        """
        Delete conversation history.
        """

        st.session_state[
            self.MESSAGE_KEY
        ] = []



    def export(self) -> list[dict]:
        """
        Export conversation.

        Useful later for:
        - evaluation
        - saving results
        - experiments
        """

        return self.get_messages()



session = SessionService()

