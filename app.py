import streamlit as st
from agents import set_default_openai_key

from ui_components import inject_css
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
inject_css()


# Initialize session state via centralized defaults
defaults = ensure_defaults(build_defaults())

# If the user provided an API key, register it with the Agents SDK.
api_key = st.session_state.get("api_key")
if api_key:
    try:
        # Avoid enabling tracing by default when using user-provided keys.
        set_default_openai_key(api_key, use_for_tracing=False)
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
