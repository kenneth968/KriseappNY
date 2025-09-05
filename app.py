import os
import streamlit as st
from agents import set_default_openai_key

from views.start_page import show as show_start
from views.chat_page import show as show_chat
from views.feedback_page import show as show_feedback
from state import build_defaults, ensure_defaults


# Basic page setup and styles
st.set_page_config(
    page_title="Sit Kafe – Kriseøvelse",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# Initialize session state via centralized defaults
defaults = ensure_defaults(build_defaults())

# If the user provided an API key, prefer it; otherwise, use server key only after auth.
# Prefer Streamlit Secrets on Community Cloud, fallback to env vars locally.
server_key = (
    (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    or (st.secrets.get("SERVER_OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("SERVER_OPENAI_API_KEY")
)
auth_required = bool(
    (st.secrets.get("AUTH_PASSWORD") if hasattr(st, "secrets") else None)
    or os.getenv("AUTH_PASSWORD")
)
api_key = st.session_state.get("api_key")
try:
    if api_key:
        # Avoid enabling tracing by default when using user-provided keys.
        set_default_openai_key(api_key, use_for_tracing=False)
    elif server_key and (not auth_required or st.session_state.get("authenticated")):
        set_default_openai_key(server_key, use_for_tracing=False)
except Exception:
    # Silently ignore; downstream calls will error visibly if key is invalid.
    pass


# Simple router
page = st.session_state.get("page", "start")
if page == "start":
    show_start(defaults)
elif page == "chat":
    show_chat(defaults)
else:
    show_feedback(defaults)
