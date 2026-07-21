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


SNIPPET_LABELS = {
    "diabetes": "General / Adult",
    "diabetes_type1_pediatric": "Type 1 (Pediatric)",
    "diabetes_gestational": "Gestational",
    "diabetes_type2_lifestyle": "Type 2 (Lifestyle)",
    "diabetes_elderly_polypharmacy": "Elderly / Polypharmacy",
}


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

        available = pipeline.available_snippets()

        if not available:

            st.warning("No medical texts found in data/snippets/.")

        else:

            if (
                "selected_snippet" not in st.session_state
                or st.session_state["selected_snippet"] not in available
            ):

                default = (
                    pipeline.DEFAULT_SNIPPET
                    if pipeline.DEFAULT_SNIPPET in available
                    else available[0]
                )

                st.session_state["selected_snippet"] = default

            selected = st.selectbox(
                "Medical text",
                options=available,
                index=available.index(
                    st.session_state["selected_snippet"]
                ),
                format_func=lambda name: SNIPPET_LABELS.get(
                    name,
                    name.replace("_", " ").title(),
                ),
                label_visibility="collapsed",
            )

            if selected != st.session_state["selected_snippet"]:

                st.session_state["selected_snippet"] = selected

                # A different medical text means a different domain -
                # old history/context wouldn't make sense to carry over.
                session.clear()
                interaction.reset_all()
                pipeline.reset_dialogue()

                st.rerun()

        st.divider()

        st.subheader("Pipeline")

        st.success("LLM")

        st.success("Prolog")

        st.success("Dialogue")

        st.success("Translator")