import streamlit as st

from ui_components import inject_css
from views.start_page import show as show_start
from views.chat_page import show as show_chat
from views.feedback_page import show as show_feedback
from state import build_defaults, ensure_defaults


# Basic page setup and styles
st.set_page_config(page_title="Sit Kafe - Kriseovelse", page_icon="🗨️")
inject_css()


# Initialize session state via centralized defaults
defaults = ensure_defaults(build_defaults())


# Simple router
page = st.session_state.get("page", "start")
if page == "start":
    show_start(defaults)
elif page == "chat":
    show_chat(defaults)
else:
    show_feedback(defaults)

