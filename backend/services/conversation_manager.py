# conversation_manager.py
# Manages in-memory chat session histories, pinned items, favorites, and exports.
import time
from typing import List, Dict, Any

class ConversationManager:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._context_memory: Dict[str, Any] = {}

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the full log history of user and AI messages."""
        return self._history

    def add_message(self, role: str, message: str, payload: Any = None) -> Dict[str, Any]:
        """Appends a new message record to the session history.
        
        Args:
            role: Either 'user' or 'assistant'.
            message: Text message body.
            payload: Structured payload if role is assistant.
            
        Returns:
            The created message dictionary.
        """
        record = {
            "id": f"msg-{int(time.time() * 1000)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "message": message,
            "payload": payload,
            "pinned": False,
            "favorite": False
        }
        self._history.append(record)
        return record

    def toggle_pin(self, message_id: str) -> bool:
        """Pins or unpins a message in history."""
        for msg in self._history:
            if msg["id"] == message_id:
                msg["pinned"] = not msg["pinned"]
                return msg["pinned"]
        return False

    def toggle_favorite(self, message_id: str) -> bool:
        """Toggles favorite state on a message."""
        for msg in self._history:
            if msg["id"] == message_id:
                msg["favorite"] = not msg["favorite"]
                return msg["favorite"]
        return False

    def update_context(self, key: str, value: Any) -> None:
        """Sets a context memory parameter (like active filters)."""
        self._context_memory[key] = value

    def get_context(self, key: str) -> Any:
        return self._context_memory.get(key)

    def clear(self) -> None:
        self._history.clear()
        self._context_memory.clear()

# Global conversation manager instance
conversation_manager = ConversationManager()
