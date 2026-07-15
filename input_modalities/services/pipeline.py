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

            if "WaitingForUserInput" in message:

                question = "Additional information required"

                # Janus message format:
                #
                # Python 'WaitingForUserInput':
                #   Enter random plasma glucose (mg/dL):
                #
                # We take the first useful line after the exception message.

                lines = message.splitlines()

                for line in lines:

                    clean = line.strip()

                    if (
                            clean
                            and not clean.startswith("Python")
                            and not clean.startswith("File")
                            and not clean.startswith("raise")
                            and "stack" not in clean
                            and "..." not in clean
                    ):
                        question = clean
                        break

                return {

                    "status": "waiting",

                    "question": question,

                    "modality": "numeric",

                    "options": None

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


            interaction.request(
                question=execution["question"],
                modality=execution["modality"],
                options=execution["options"]
            )


            return PipelineResponse(

                answer="",

                query=prolog_query,

                raw_result=None,

                sources=[]

            )



        result = execution["result"]



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