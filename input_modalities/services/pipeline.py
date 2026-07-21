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


    def __init__(self):

        self.kb_path = Path(
            "prolog/generated_kb/diabetes_diagnosis.pl"
        )


        self.session_memory = SessionMemory()

        self.state_manager = StateManager()

        self.context_tracker = ContextTracker(
            self.session_memory
        )

        self.followup_manager = FollowupManager()

        self.modality_handler = DialogueModalityHandler()

        self._loaded = False

        # Resume state (which query to re-run once the user answers a
        # pending question) lives in `interaction` / st.session_state,
        # NOT on this object - `pipeline` is one shared instance for
        # the whole server process, so storing it here would leak
        # between concurrent browser tabs/sessions.



    def initialize(self):

        if self._loaded:
            return



        project_root = str(Path.cwd())

        if project_root not in sys.path:

            sys.path.insert(
                0,
                project_root
            )


        # load Janus callbacks
        import prolog_bridge



        print("Building knowledge base...")


        with open(
            "data/snippets/diabetes.txt",
            encoding="utf-8"
        ) as file:

            medical_text = file.read()



        kb_code = generate_prolog_kb(
            medical_text
        )



        self.kb_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        self.kb_path.write_text(
            kb_code,
            encoding="utf-8"
        )



        print("Loading Prolog KB...")


        janus.consult(
            str(self.kb_path)
        )



        self._loaded = True


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
        question: str
    ) -> PipelineResponse:


        print(
            "\n========== PIPELINE START =========="
        )


        self.initialize()



        print(
            "Generating Prolog query..."
        )



        resolved = (
            self.context_tracker
            .resolve_context(question)
        )


        enhanced_question = resolved["question"]



        kb_text = self.kb_path.read_text(
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
            execution["result"]
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
            execution["result"]
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
        result
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
                    "title": "diabetes.txt",
                    "score": 1.0
                }
            ]
        )


pipeline = MedicalPipeline()