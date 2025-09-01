import streamlit as st
from state import reset_to_start, restart_chat


def show(defaults: dict):
    st.title("Kriseøvelse – Feedback")
    meta = st.session_state.get("last_meta", {}) or {}
    turns = st.session_state.get("turns", 0)
    diff = st.session_state.get("difficulty", "")

    st.markdown(
        f"<div style='font-size:18px; color:#334155; margin-bottom:8px;'>Runder brukt: <b>{turns}</b> – Vanskelighetsgrad: <b>{diff}</b></div>",
        unsafe_allow_html=True,
    )

    result = meta.get("scenarioresultat")
    feedback = meta.get("tilbakemelding")
    if result and isinstance(result, dict) and result.get("content"):
        st.success(result.get("content"))
    else:
        st.info("Ingen scenarioresultat registrert ennå.")
    if feedback and isinstance(feedback, dict) and feedback.get("content"):
        st.warning(feedback.get("content"))

    st.divider()
    st.subheader("Hva vil du gjøre videre?")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Til start", use_container_width=True):
            reset_to_start(defaults)
            st.rerun()
    with c2:
        if st.button("Prøv på nytt (samme innstillinger)", use_container_width=True):
            restart_chat()
            st.rerun()
    with c3:
        if st.button("Se chat-logg", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()

