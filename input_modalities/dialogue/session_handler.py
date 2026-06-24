# dialogue/session_handler.py

from typing import List, Dict, Any
from collections import deque


class SessionMemory:
    """
    Stores full conversation history for a single session.

    This acts as short-term + structured memory.
    """

    def __init__(self, max_size: int = 50):
        self.history = deque(maxlen=max_size)

    def add(self, entry: Dict[str, Any]) -> None:
        """
        Add a new interaction to memory.
        """
        self.history.append(entry)

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def get_last(self) -> Dict[str, Any]:
        if not self.history:
            return {}
        return self.history[-1]

    def clear(self) -> None:
        self.history.clear()