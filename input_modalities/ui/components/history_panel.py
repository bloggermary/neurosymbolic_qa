"""
Conversation history and save/export controls.

Surfaces the dialogue layer (SessionMemory, StateManager) in the UI:
- render_history_panel: lists past question/answer turns.
- render_save_controls: exports the chat or the current dialogue
  context to a JSON file the user can download.
"""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from services.session_service import session
from services.pipeline import pipeline


def render_history_panel() -> None:
    """
    Show past question/answer turns from the dialogue layer's
    SessionMemory (dialogue/session_handler.py).
    """

    st.subheader(" History")

    turns = pipeline.session_memory.get_all()

    if not turns:

        st.caption("No questions asked yet.")
        return

    with st.expander(
        f"{len(turns)} previous turn(s)",
        expanded=False,
    ):

        for index, turn in enumerate(reversed(turns), start=1):

            st.markdown(
                f"**{len(turns) - index + 1}. {turn.get('question', '')}**"
            )

            st.caption(
                turn.get("answer", "")
            )

            if turn.get("prolog_query"):

                with st.expander(
                    "Prolog query",
                    expanded=False,
                ):

                    st.code(
                        turn["prolog_query"],
                        language="prolog",
                    )

            st.divider()



def render_save_controls() -> None:
    """
    Export controls backed by the dialogue layer.

    - "Save Chat" exports the full rendered conversation
      (services.session_service.session).
    - "Save Current Context" exports the dialogue layer's current
      turn snapshot (dialogue/state_manager.py).
    """

    st.subheader(" Save")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    chat_export = json.dumps(
        session.get_messages(),
        indent=2,
        default=str,
    )

    st.download_button(
        "Save Chat",
        data=chat_export,
        file_name=f"chat_{timestamp}.json",
        mime="application/json",
        use_container_width=True,
    )

    context_export = json.dumps(
        pipeline.state_manager.get_state(),
        indent=2,
        default=str,
    )

    st.download_button(
        "Save Current Context",
        data=context_export,
        file_name=f"context_{timestamp}.json",
        mime="application/json",
        use_container_width=True,
    )
