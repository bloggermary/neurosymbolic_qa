"""
Reusable chat message component.
"""

from __future__ import annotations

import streamlit as st


def render_message(message: dict) -> None:
    """
    Render a single chat message.

    Parameters
    ----------
    message:
        Dictionary containing role, content and optional metadata.
    """

    role = message["role"]
    content = message["content"]

    avatar = "🧑" if role == "user" else "🧠"

    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

        if role == "assistant":

            reasoning = message.get("reasoning", {})

            if reasoning:

                with st.expander("View reasoning", expanded=False):

                    if reasoning.get("query"):
                        st.markdown("**Generated Prolog Query**")
                        st.code(reasoning["query"], language="prolog")

                    if reasoning.get("result") is not None:
                        st.markdown("**Raw Prolog Result**")
                        st.code(str(reasoning["result"]))

                    if reasoning.get("error"):
                        st.markdown("**Error**")
                        st.code(str(reasoning["error"]))