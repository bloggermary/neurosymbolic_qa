"""
Loading indicator shown while reasoning.
"""

from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def reasoning_status():
    """
    Display reasoning progress.

    Usage
    -----

    with reasoning_status():

        ...
    """

    with st.status("Reasoning...", expanded=True) as status:

        st.write("Generating Prolog query...")

        yield

        st.write("Executing symbolic reasoning...")

        st.write("Translating answer...")

        status.update(
            label="Completed",
            state="complete",
            expanded=False,
        )