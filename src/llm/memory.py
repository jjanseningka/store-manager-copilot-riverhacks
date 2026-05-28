"""Conversation memory — session + persistent preferences.

Stores:
1. Session memory: conversation history per session (in-memory)
2. User preferences: persistent settings per store manager (JSON file)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from datetime import datetime


MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "memory"


class ConversationMemory:
    """Manages session history and persistent user preferences."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[dict[str, Any]]] = {}
        self._preferences: dict[str, dict[str, Any]] = {}
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._load_preferences()

    # ------------------------------------------------------------------
    # Session memory
    # ------------------------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Record a message in session history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get full conversation history for a session."""
        return self._sessions.get(session_id, [])

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """Get session metadata."""
        history = self._sessions.get(session_id, [])
        return {
            "session_id": session_id,
            "message_count": len(history),
            "started": history[0]["timestamp"] if history else None,
            "last_message": history[-1]["timestamp"] if history else None,
        }

    def clear_session(self, session_id: str) -> None:
        """Clear a specific session."""
        self._sessions.pop(session_id, None)

    # ------------------------------------------------------------------
    # Persistent preferences
    # ------------------------------------------------------------------

    def _prefs_file(self) -> Path:
        return MEMORY_DIR / "preferences.json"

    def _load_preferences(self) -> None:
        path = self._prefs_file()
        if path.exists():
            try:
                self._preferences = json.loads(path.read_text())
            except (json.JSONDecodeError, IOError):
                self._preferences = {}

    def _save_preferences(self) -> None:
        self._prefs_file().write_text(json.dumps(self._preferences, indent=2))

    def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Get all preferences for a user."""
        return self._preferences.get(user_id, {})

    def set_preference(self, user_id: str, key: str, value: Any) -> None:
        """Set a single preference."""
        if user_id not in self._preferences:
            self._preferences[user_id] = {}
        self._preferences[user_id][key] = value
        self._preferences[user_id]["_updated"] = datetime.now().isoformat()
        self._save_preferences()

    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get a single preference value."""
        return self._preferences.get(user_id, {}).get(key, default)

    # ------------------------------------------------------------------
    # Context for LLM
    # ------------------------------------------------------------------

    def get_context_for_llm(self, session_id: str, user_id: str) -> str:
        """Build context string from memory to inject into LLM system prompt."""
        parts = []

        # User preferences
        prefs = self.get_preferences(user_id)
        if prefs:
            pref_items = {k: v for k, v in prefs.items() if not k.startswith("_")}
            if pref_items:
                parts.append("## User Preferences")
                for k, v in pref_items.items():
                    parts.append(f"- **{k}**: {v}")

        # Recent session topics (last 5 messages)
        history = self.get_session_history(session_id)
        if len(history) > 2:
            recent_questions = [
                m["content"][:100]
                for m in history[-10:]
                if m["role"] == "user"
            ]
            if recent_questions:
                parts.append("\n## Recent Questions This Session")
                for q in recent_questions[-5:]:
                    parts.append(f"- {q}")

        return "\n".join(parts) if parts else ""


# Singleton instance
_memory = ConversationMemory()


def get_memory() -> ConversationMemory:
    return _memory
