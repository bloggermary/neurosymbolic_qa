"""
Sidebar component.
"""

from __future__ import annotations

import streamlit as st

from services.session_service import session
from services.interaction_service import interaction
from services.pipeline import pipeline

from ui.components.history_panel import (
    render_history_panel,
    render_save_controls,
)


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
            interaction.reset_all()
            pipeline.reset_dialogue()
            st.rerun()

        st.divider()

        render_history_panel()

        st.divider()

        render_save_controls()

        st.divider()

        st.subheader("Knowledge Base")

        st.info("Diabetes")

        st.divider()

        st.subheader("Pipeline")

        st.success("LLM")

        st.success("Prolog")

        st.success("Dialogue")

        st.success("Translator")