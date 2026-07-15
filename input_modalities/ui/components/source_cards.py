"""
Displays retrieved sources.
"""

from __future__ import annotations

import streamlit as st


def render_sources(sources: list[dict]) -> None:
    """
    Display retrieved knowledge sources.

    Parameters
    ----------
    sources:
        List of dictionaries.

        Example

        [
            {
                "title":"diabetes.txt",
                "score":0.92
            }
        ]
    """

    if not sources:
        return

    st.markdown("### Sources")

    columns = st.columns(len(sources))

    for column, source in zip(columns, sources):

        with column:

            with st.container(border=True):

                st.markdown(f"**📄 {source['title']}**")

                if "score" in source:
                    st.caption(
                        f"Similarity: {source['score']:.2f}"
                    )