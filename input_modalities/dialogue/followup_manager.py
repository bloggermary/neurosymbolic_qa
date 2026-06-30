# dialogue/followup_manager.py

from typing import Dict, List


class FollowupManager:
    """
    Stores and retrieves follow-up questions.
    """

    def __init__(self):
        self.store_data: Dict[str, List[str]] = {}

    def store(self, question: str, followups: List[str]) -> None:
        """
        Store follow-ups linked to a question.
        """
        self.store_data[question] = followups

    def get(self, question: str) -> List[str]:
        return self.store_data.get(question, [])

    def get_all(self) -> Dict[str, List[str]]:
        return self.store_data