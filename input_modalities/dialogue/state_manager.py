# dialogue/state_manager.py

from typing import Dict, Any


class StateManager:
    """
    Tracks current conversation state.
    """

    def __init__(self):
        self.state = {
            "question": None,
            "answer": None,
            "modality": None,
            "prolog_query": None
        }

    def update(self, question: str, answer: Any, modality: str = None, prolog_query: str = None):
        self.state["question"] = question
        self.state["answer"] = answer
        self.state["modality"] = modality
        self.state["prolog_query"] = prolog_query

    def get_state(self) -> Dict[str, Any]:
        return self.state

    def reset(self):
        for k in self.state:
            self.state[k] = None