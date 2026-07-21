"""
Interaction service.

Acts as a bridge between:
- Prolog/Pipeline requesting information
- Streamlit UI collecting the answer

All state here is stored in st.session_state, not on the object
instance. A previous version stored it as plain instance attributes,
which meant every browser tab/session shared the SAME pending
question and answer cache (since `interaction` is one module-level
object for the whole server process). Two tabs open at once would
silently overwrite each other's pending question - one tab's answer
could clear the question another tab was still waiting to render, or
a freshly raised WaitingForUserInput could be wiped before the
"waiting" check saw it. Streamlit's session_state is already scoped
per browser session (via its ScriptRunContext), so backing state with
it - even though this module is reached deep inside a Prolog
callback - keeps each tab's dialogue fully independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st


NO_ANSWER = object()


_PENDING_KEY = "interaction_pending_question"
_ANSWERS_KEY = "interaction_answers"
_RESUME_KEY = "interaction_resume_context"


@dataclass
class PendingQuestion:
    """
    Represents a question waiting for the user.
    """

    question: str
    modality: str
    options: list | dict | None = None
    answer: Any | None = None


class InteractionService:

    def _ensure_state(self):

        if _PENDING_KEY not in st.session_state:
            st.session_state[_PENDING_KEY] = None

        if _ANSWERS_KEY not in st.session_state:
            st.session_state[_ANSWERS_KEY] = {}

        if _RESUME_KEY not in st.session_state:
            st.session_state[_RESUME_KEY] = None



    @property
    def pending_question(self) -> PendingQuestion | None:

        self._ensure_state()
        return st.session_state[_PENDING_KEY]



    @pending_question.setter
    def pending_question(self, value: PendingQuestion | None):

        self._ensure_state()
        st.session_state[_PENDING_KEY] = value



    @property
    def answers(self) -> dict[str, Any]:

        self._ensure_state()
        return st.session_state[_ANSWERS_KEY]



    def request(
        self,
        question: str,
        modality: str,
        options=None,
    ):
        """
        Called by Prolog bridge when input is required.
        """

        self.pending_question = PendingQuestion(
            question=question,
            modality=modality,
            options=options,
        )



    def has_question(self) -> bool:

        return self.pending_question is not None



    def get_question(self):

        return self.pending_question



    def set_answer(
        self,
        answer: Any
    ):
        """
        Called by Streamlit after user submits input.
        """

        pending = self.pending_question

        if pending:

            pending.answer = answer
            self.pending_question = pending



    def has_answer(self) -> bool:

        pending = self.pending_question

        return (
            pending is not None
            and pending.answer is not None
        )



    def get_answer(self):

        pending = self.pending_question

        if pending:

            return pending.answer

        return None



    def clear(self):

        self.pending_question = None



    def reset_answer(self):

        """
        Keep the question but remove old answer.
        """

        pending = self.pending_question

        if pending:

            pending.answer = None
            self.pending_question = pending



    def remember(self, question: str, value: Any):
        """
        Cache a resolved answer so re-running the Prolog query
        doesn't ask the same question twice.
        """

        answers = self.answers
        answers[question] = value
        st.session_state[_ANSWERS_KEY] = answers



    def get_cached_answer(self, question: str):
        """
        Return the cached answer for `question`, or NO_ANSWER if
        it hasn't been answered yet in this session.
        """

        return self.answers.get(question, NO_ANSWER)



    def set_resume_context(self, query: str, question: str, enhanced_question: str):
        """
        Remember what to re-run once the user answers a pending
        question. Session-scoped so concurrent tabs never mix up
        which query they're each resuming.
        """

        self._ensure_state()

        st.session_state[_RESUME_KEY] = {
            "query": query,
            "question": question,
            "enhanced_question": enhanced_question,
        }



    def get_resume_context(self):

        self._ensure_state()
        return st.session_state[_RESUME_KEY]



    def reset_all(self):
        """
        Start a fresh reasoning session (e.g. "New Chat").
        """

        st.session_state[_PENDING_KEY] = None
        st.session_state[_ANSWERS_KEY] = {}
        st.session_state[_RESUME_KEY] = None



interaction = InteractionService()
