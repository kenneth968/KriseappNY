from typing import Any, Dict

import streamlit as st

from config import MAX_TURNS


def build_defaults() -> Dict[str, Any]:
    """Return the canonical default session state values.

    Values like page and difficulty respect any existing session values to
    preserve navigation and user preference across reruns.
    """
    return {
        "history": [],
        "ended": False,
        "started": False,
        "user_name": "",
        "api_key": st.session_state.get("api_key", ""),
        "turns": 0,
        "awaiting_user": False,
        "last_meta": {},
        "page": st.session_state.get("page", "start"),
        "difficulty": st.session_state.get("difficulty", "Medium"),
        "max_turns": st.session_state.get("max_turns", MAX_TURNS),
    }


def ensure_defaults(defaults: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ensure any missing keys are initialized in session state.

    Returns the defaults dict that was applied (either provided or built).
    """
    if defaults is None:
        defaults = build_defaults()
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    return defaults


def reset_to_start(defaults: Dict[str, Any] | None = None) -> None:
    """Reset all tracked state back to defaults and navigate to start page."""
    if defaults is None:
        defaults = build_defaults()
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state.page = "start"


def restart_chat() -> None:
    """Start a fresh run while preserving user settings like name/difficulty."""
    st.session_state.history = []
    st.session_state.ended = False
    st.session_state.turns = 0
    st.session_state.last_meta = {}
    st.session_state.started = True
    st.session_state.awaiting_user = True
    st.session_state.page = "chat"
