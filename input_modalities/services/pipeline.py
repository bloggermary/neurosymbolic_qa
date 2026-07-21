"""
Pipeline service.

Connects:
- Streamlit UI
- LLM query generation
- Prolog reasoning
- Dialogue memory
- Janus Python callbacks
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sys

import janus_swi as janus
import streamlit as st


from llm.kb_generator import generate_prolog_kb
from llm.query_generator import generate_query
from llm.response_translator import translate_result


from dialogue.session_handler import SessionMemory
from dialogue.state_manager import StateManager
from dialogue.context_tracker import ContextTracker
from dialogue.followup_manager import FollowupManager
from dialogue.modality_handler import DialogueModalityHandler


from services.interaction_service import interaction

from prolog_bridge import WaitingForUserInput



@dataclass(slots=True)
class PipelineResponse:

    answer: str
    query: str
    raw_result: Any
    sources: list[dict]



class MedicalPipeline:


    DEFAULT_SNIPPET = "diabetes"

    SNIPPETS_DIR = Path("data/snippets")
    GENERATED_DIR = Path("prolog/generated_kb")

    def __init__(self):

        self.modality_handler = DialogueModalityHandler()

        # Which snippet's KB is currently consulted into the (single,
        # process-wide) embedded Prolog engine. janus_swi embeds one
        # SWI-Prolog interpreter per process, not per browser session,
        # so only one knowledge base can be active at a time - switching
        # snippets rebuilds and re-consults for the whole process. Fine
        # for this single-active-demo-user setup; would need a real
        # per-session Prolog engine to safely serve two different
        # snippets to two concurrent users at once.
        self._loaded_snippet: str | None = None



    def available_snippets(self) -> list[str]:
        """
        Names (without .txt) of every medical text under data/snippets.
        """

        return sorted(
            path.stem
            for path in self.SNIPPETS_DIR.glob("*.txt")
        )



    def kb_path_for(self, snippet_name: str) -> Path:

        return self.GENERATED_DIR / f"{snippet_name}.pl"

        # Resume state (which query to re-run once the user answers a
        # pending question) lives in `interaction` / st.session_state,
        # NOT on this object - `pipeline` is one shared instance for
        # the whole server process, so storing it here would leak
        # between concurrent browser tabs/sessions.
        #
        # session_memory / state_manager / context_tracker /
        # followup_manager are dialogue-layer objects with the exact
        # same problem: they hold per-conversation state (history,
        # last turn, follow-ups), so they're exposed as properties
        # backed by st.session_state below instead of being set here,
        # keeping each browser tab's dialogue memory independent.



    @property
    def session_memory(self) -> SessionMemory:

        if "pipeline_session_memory" not in st.session_state:
            st.session_state["pipeline_session_memory"] = SessionMemory()

        return st.session_state["pipeline_session_memory"]



    @property
    def state_manager(self) -> StateManager:

        if "pipeline_state_manager" not in st.session_state:
            st.session_state["pipeline_state_manager"] = StateManager()

        return st.session_state["pipeline_state_manager"]



    @property
    def context_tracker(self) -> ContextTracker:

        if "pipeline_context_tracker" not in st.session_state:
            st.session_state["pipeline_context_tracker"] = ContextTracker(
                self.session_memory
            )

        return st.session_state["pipeline_context_tracker"]



    @property
    def followup_manager(self) -> FollowupManager:

        if "pipeline_followup_manager" not in st.session_state:
            st.session_state["pipeline_followup_manager"] = FollowupManager()

        return st.session_state["pipeline_followup_manager"]



    def reset_dialogue(self):
        """
        Start a fresh conversation: wipe history, last-turn state, and
        stored follow-ups for THIS browser session only.
        """

        st.session_state["pipeline_session_memory"] = SessionMemory()
        st.session_state["pipeline_state_manager"] = StateManager()
        st.session_state["pipeline_context_tracker"] = ContextTracker(
            st.session_state["pipeline_session_memory"]
        )
        st.session_state["pipeline_followup_manager"] = FollowupManager()



    def initialize(self, snippet_name: str | None = None):

        snippet_name = snippet_name or self.DEFAULT_SNIPPET

        if self._loaded_snippet == snippet_name:
            return



        project_root = str(Path.cwd())

        if project_root not in sys.path:

            sys.path.insert(
                0,
                project_root
            )


        # load Janus callbacks
        import prolog_bridge



        print(f"Building knowledge base for '{snippet_name}'...")


        snippet_path = self.SNIPPETS_DIR / f"{snippet_name}.txt"

        with open(
            snippet_path,
            encoding="utf-8"
        ) as file:

            medical_text = file.read()



        kb_code = generate_prolog_kb(
            medical_text
        )



        kb_path = self.kb_path_for(snippet_name)

        kb_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        kb_path.write_text(
            kb_code,
            encoding="utf-8"
        )



        print("Loading Prolog KB...")


        janus.consult(
            str(kb_path)
        )



        self._loaded_snippet = snippet_name


        print("Pipeline initialized.")

    def _execute_query(
            self,
            query: str
    ):

        query = query.rstrip(".").strip()

        try:

            result = janus.query_once(query)

            return {
                "status": "completed",
                "result": result
            }


        except Exception as error:

            message = str(error)

            print(
                "Caught Prolog/Python exception:",
                message
            )

            # WaitingForUserInput crosses the py_call boundary into
            # Prolog and back out as a generic Prolog exception - only
            # its string message survives, so modality/options can't be
            # recovered from `error` here. Instead, prolog_bridge.ask_*
            # registers the pending question with `interaction` itself
            # (with full fidelity) before raising. We check both that
            # marker AND the exception text as a safety net, in case the
            # pending question was somehow already consumed/cleared by
            # the time we get here.

            if interaction.has_question() or "WaitingForUserInput" in message:

                return {
                    "status": "waiting"
                }

            raise error


    def ask(
        self,
        question: str,
        snippet_name: str | None = None,
    ) -> PipelineResponse:


        snippet_name = snippet_name or self.DEFAULT_SNIPPET


        print(
            "\n========== PIPELINE START =========="
        )


        self.initialize(snippet_name)



        print(
            "Generating Prolog query..."
        )



        resolved = (
            self.context_tracker
            .resolve_context(question)
        )


        enhanced_question = resolved["question"]



        kb_text = self.kb_path_for(snippet_name).read_text(
            encoding="utf-8"
        )



        prolog_query = generate_query(
            enhanced_question,
            kb_text
        ).strip()



        print(
            "Generated query:",
            prolog_query
        )



        print(
            "Executing Prolog..."
        )



        execution = self._execute_query(
            prolog_query
        )



        print(
            "Execution:",
            execution
        )



        # ----------------------------------
        # Prolog needs user input
        # ----------------------------------

        if execution["status"] == "waiting":

            # Remember what to re-run once the user answers.
            # (The pending question itself was already registered with
            # `interaction` by prolog_bridge.ask_* - see _execute_query.)
            interaction.set_resume_context(
                query=prolog_query,
                question=question,
                enhanced_question=enhanced_question,
                snippet_name=snippet_name,
            )

            return PipelineResponse(
                answer="",
                query=prolog_query,
                raw_result=None,
                sources=[]
            )

        return self._finalize(
            question,
            enhanced_question,
            prolog_query,
            execution["result"],
            snippet_name,
        )



    def resume(
        self,
        answer
    ) -> PipelineResponse:
        """
        Called after the user answers a pending Prolog question.

        Prolog can't be paused and resumed mid-query, so this stores
        the answer in the interaction cache and re-executes the same
        query from scratch. Already-answered questions are skipped
        (prolog_bridge returns the cached value instead of asking
        again), so reasoning simply continues past them.
        """

        pending = interaction.get_question()

        if pending is None:
            raise RuntimeError("No pending question to resume")

        converted = self._coerce_answer(
            modality=pending.modality,
            raw=answer
        )

        interaction.remember(
            pending.question,
            converted
        )

        interaction.clear()

        resume_context = interaction.get_resume_context()

        if resume_context is None:
            raise RuntimeError("No resume context for this session")

        resume_query = resume_context["query"]

        execution = self._execute_query(
            resume_query
        )

        if execution["status"] == "waiting":

            # Pending question already registered by prolog_bridge.ask_*.
            return PipelineResponse(
                answer="",
                query=resume_query,
                raw_result=None,
                sources=[]
            )

        return self._finalize(
            resume_context["question"],
            resume_context["enhanced_question"],
            resume_query,
            execution["result"],
            resume_context.get("snippet_name") or self.DEFAULT_SNIPPET,
        )



    @staticmethod
    def _coerce_answer(modality: str, raw):
        """
        Convert a widget value into what the Prolog callback
        (and py_call unification) expects.
        """

        if modality == "boolean":
            return str(raw).strip().lower() in ("yes", "true", "1")

        if modality in ("numeric", "duration", "range", "scale"):
            return float(raw)

        return raw



    def _finalize(
        self,
        question: str,
        enhanced_question: str,
        prolog_query: str,
        result,
        snippet_name: str | None = None,
    ) -> PipelineResponse:
        """
        Shared completion path: translate the Prolog result, update
        dialogue memory, and build the response returned to the UI.
        """

        print(
            "Reached translation step"
        )

        answer = translate_result(
            enhanced_question,
            prolog_query,
            result
        )

        self.state_manager.update(
            question=question,
            answer=answer,
            modality=None,
            prolog_query=prolog_query
        )

        self.session_memory.add(
            {
                "question": question,
                "answer": answer,
                "modality": None,
                "prolog_query": prolog_query
            }
        )

        self.followup_manager.store(
            question,
            []
        )

        response = {
            "answer": answer,
            "style": "default"
        }

        response = (
            self.modality_handler
            .adjust_response_behavior(
                modality=None,
                response=response
            )
        )

        return PipelineResponse(
            answer=response["answer"],
            query=prolog_query,
            raw_result=result,
            sources=[
                {
                    "title": f"{snippet_name or self.DEFAULT_SNIPPET}.txt",
                    "score": 1.0
                }
            ]
        )


pipeline = MedicalPipeline()