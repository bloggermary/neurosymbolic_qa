"""
Sidebar component.
"""

from __future__ import annotations

import re

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


def _sanitize_snippet_name(raw: str) -> str:
    """
    Turn free-text input into a safe filename stem: lowercase,
    alphanumeric/underscore only. Prevents path traversal (e.g. "../x")
    since the result never contains "/", ".", or spaces.
    """

    name = raw.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


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

        with st.expander(
            "➕ Add new medical text",
            expanded=False,
        ):

            new_name = st.text_input(
                "Name",
                key="new_snippet_name",
                placeholder="e.g. diabetes_renal",
            )

            uploaded = st.file_uploader(
                "Upload a .txt file",
                type=["txt"],
                key="new_snippet_upload",
            )

            pasted_text = st.text_area(
                "...or paste the text directly",
                key="new_snippet_text",
                height=150,
            )

            if st.button(
                "Save medical text",
                use_container_width=True,
            ):

                safe_name = _sanitize_snippet_name(new_name)

                content = None

                if uploaded is not None:
                    content = uploaded.read().decode("utf-8")
                elif pasted_text.strip():
                    content = pasted_text

                if not safe_name:

                    st.error(
                        "Please provide a name (letters/numbers only)."
                    )

                elif not content:

                    st.error(
                        "Please upload a .txt file or paste some text."
                    )

                else:

                    new_path = pipeline.SNIPPETS_DIR / f"{safe_name}.txt"

                    if new_path.exists():

                        st.error(
                            f"'{safe_name}' already exists. Choose a "
                            "different name."
                        )

                    else:

                        new_path.parent.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        new_path.write_text(
                            content,
                            encoding="utf-8",
                        )

                        st.session_state["selected_snippet"] = safe_name

                        # New text = new domain - start with a clean slate.
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