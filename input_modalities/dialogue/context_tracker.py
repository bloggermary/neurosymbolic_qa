# dialogue/context_tracker.py

from typing import Dict, Any


class ContextTracker:
    """
    Tracks semantic context between turns.
    """

    def __init__(self, memory):
        self.memory = memory

    def resolve_context(self, question: str) -> Dict[str, Any]:
        """
        Enhances question using previous conversation context.
        """

        history = self.memory.get_all()

        if not history:
            return {
                "question": question,
                "context_used": False
            }

        last = history[-1]

        return {
            "question": question,
            "previous_question": last.get("question"),
            "previous_answer": last.get("answer"),
            "previous_modality": last.get("modality"),
            "context_used": True
        }