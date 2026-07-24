"""
Main chat page for the NeuroSymbolic Medical Assistant.

Responsible for:
- Rendering Streamlit UI
- Receiving user messages
- Displaying pipeline responses
- Handling interactive modality questions
"""

from __future__ import annotations

import streamlit as st


from services.pipeline import pipeline
from services.session_service import session
from services.interaction_service import interaction


from ui.components.chat_window import render_chat_window
from ui.components.loading_spinner import reasoning_status
from ui.components.sidebar import render_sidebar
from ui.components.source_cards import render_sources


from ui.styles.css import load_css



def display_response(response) -> None:
    """
    Render a completed pipeline response and store it in the
    conversation history. Shared by the initial question flow and
    the "answer a pending question" resume flow.
    """

    st.markdown(
        response.answer
    )

    if response.sources:

        render_sources(
            response.sources
        )

    with st.expander(
        "View reasoning",
        expanded=False
    ):

        st.markdown(
            "**Generated Prolog Query**"
        )

        st.code(
            response.query,
            language="prolog"
        )

        st.markdown(
            "**Raw Prolog Result**"
        )

        st.code(
            str(response.raw_result)
        )

    session.add_assistant(
        content=response.answer,
        reasoning={
            "query": response.query,
            "result": response.raw_result,
        },
        sources=response.sources,
    )



def render_pending_question():
    """
    Render input requested by Prolog, and resume reasoning once
    the user submits an answer.
    """

    if not interaction.has_question():
        return False


    pending = interaction.get_question()


    with st.chat_message("assistant", avatar="🧠"):

        st.info(
            pending.question
        )

        followups = pipeline.followups_for_pending(
            pending.question,
            pending.modality,
        )

        if followups:

            for followup in followups:

                st.caption(
                    f"💡 You might also consider asking about: "
                    f"**{followup['topic']}** "
                    f"({followup['modality'].replace('_', ' ')})"
                )


        answer = None


        if pending.modality == "numeric":

            answer = st.number_input(
                pending.question,
                key="numeric_input",
                step=1.0,
                format="%.2f",
                label_visibility="collapsed",
            )


        elif pending.modality == "boolean":

            answer = st.radio(
                pending.question,
                ["yes", "no"],
                key="boolean_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "string":

            answer = st.text_input(
                pending.question,
                key="string_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "category":

            answer = st.selectbox(
                pending.question,
                pending.options,
                key="category_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "range":

            answer = st.slider(
                pending.question,
                pending.options["min"],
                pending.options["max"],
                key="range_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "duration":

            answer = st.number_input(
                pending.question,
                min_value=0,
                step=1,
                key="duration_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "multiple_category":

            answer = st.multiselect(
                pending.question,
                pending.options,
                key="multiple_category_input",
                label_visibility="collapsed",
            )


        elif pending.modality == "multi_structured_input":

            mode = pending.options["mode"]
            groups = pending.options.get("groups") or []

            if mode == "grouping":

                group_answers = {}

                for group in groups:

                    text = st.text_area(
                        group,
                        key=f"multi_structured_group_{group}",
                    )

                    group_answers[group] = [
                        line.strip()
                        for line in text.splitlines()
                        if line.strip()
                    ]

                answer = group_answers

            else:

                text = st.text_area(
                    pending.question,
                    key="multi_structured_input",
                    help="Enter one item per line, in order.",
                    label_visibility="collapsed",
                )

                items = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip()
                ]

                if mode == "ranking":

                    answer = [
                        {"rank": index + 1, "value": item}
                        for index, item in enumerate(items)
                    ]

                else:

                    answer = items


        elif pending.modality == "multi_attribute_entity":

            entity = pending.options["entity"]
            fields = pending.options["fields"]

            field_values = {}

            for field in fields:

                key, prompt, field_type = field[0], field[1], field[2]

                widget_key = f"entity_field_{key}"

                if field_type == "int":

                    field_values[key] = st.number_input(
                        prompt,
                        step=1,
                        key=widget_key,
                    )

                elif field_type == "float":

                    field_values[key] = st.number_input(
                        prompt,
                        step=0.1,
                        format="%.2f",
                        key=widget_key,
                    )

                elif field_type == "bool":

                    field_values[key] = st.radio(
                        prompt,
                        ["yes", "no"],
                        key=widget_key,
                    ) == "yes"

                else:

                    field_values[key] = st.text_input(
                        prompt,
                        key=widget_key,
                    )

            answer = {"entity": entity, "data": field_values}


        if st.button(
            "Submit answer",
            key="submit_answer"
        ):

            try:

                with reasoning_status():

                    response = pipeline.resume(answer)

                if response.answer == "" and interaction.has_question():

                    st.rerun()

                else:

                    display_response(response)

                    st.rerun()

            except Exception as error:

                st.error(
                    "️ An unexpected error occurred while processing your answer."
                )

                with st.expander(
                    "Technical Details"
                ):

                    st.code(
                        str(error)
                    )

                interaction.clear()

                session.add_assistant(
                    content="An error occurred while processing the request.",
                    reasoning={
                        "error": str(error)
                    }
                )

                st.rerun()


    return True




def render_chat() -> None:


    st.set_page_config(
        page_title="NeuroSymbolic Medical Assistant",
        layout="centered",
    )


    st.markdown(
        load_css(),
        unsafe_allow_html=True
    )


    session.initialize()



    render_sidebar()



    st.title(
        " NeuroSymbolic Medical Assistant"
    )


    st.caption(
        "LLM + Prolog + RAG + Symbolic Reasoning"
    )


    st.divider()



    render_chat_window()



    # --------------------------------------------
    # Handle pending Prolog questions first
    # --------------------------------------------

    if render_pending_question():

        return



    question = st.chat_input(
        "Ask a medical question..."
    )


    if question is None:

        return



    with st.chat_message(
        "user",
        avatar="🧑"
    ):

        st.markdown(
            question
        )


    session.add_user(
        question
    )



    with st.chat_message(
        "assistant",
        avatar="🧠"
    ):

        try:


            with reasoning_status():

                response = pipeline.ask(
                    question,
                    snippet_name=st.session_state.get("selected_snippet"),
                )



            # ------------------------------------
            # Pipeline needs additional information
            # ------------------------------------

            if response.answer == "" and interaction.has_question():

                st.warning(
                    "Additional information required."
                )

                st.rerun()

            else:

                display_response(response)


        except Exception as error:


            st.error(
                "️ An unexpected error occurred while processing your question."
            )


            with st.expander(
                "Technical Details"
            ):

                st.code(
                    str(error)
                )

            interaction.clear()

            session.add_assistant(
                content="An error occurred while processing the request.",
                reasoning={
                    "error": str(error)
                }
            )
