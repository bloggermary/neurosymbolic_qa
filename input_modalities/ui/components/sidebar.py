"""
Sidebar component.
"""

from __future__ import annotations

import streamlit as st

from services.session_service import session


def render_sidebar() -> None:
    """
    Render application sidebar.
    """

    with st.sidebar:

        st.title("🧠 NeuroSymbolic")

        st.caption(
            "Medical Question Answering System"
        )

        st.divider()

        if st.button(
            "➕ New Chat",
            use_container_width=True,
        ):
            session.clear()
            st.rerun()

        st.divider()

        st.subheader("Knowledge Base")

        st.info("Diabetes")

        st.divider()

        st.subheader("Pipeline")

        st.success("LLM")

        st.success("Prolog")

        st.success("Dialogue")

        st.success("Translator")