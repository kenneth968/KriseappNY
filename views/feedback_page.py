import streamlit as st
from state import reset_to_start, restart_chat
from ui_components import page_header


def show(defaults: dict):
    page_header("Kriseøvelse – Feedback")
    meta = st.session_state.get("last_meta", {}) or {}
    turns = st.session_state.get("turns", 0)
    diff = st.session_state.get("difficulty", "")

    st.markdown(
        f"<div class='chip chip-primary' style='margin-right:8px;'>Runder brukt: <b>{turns}</b></div>"
        f"<div class='chip chip-muted'>Vanskelighetsgrad: <b>{diff}</b></div>",
        unsafe_allow_html=True,
    )

    result = meta.get("scenarioresultat")
    feedback = meta.get("tilbakemelding")
    if result and isinstance(result, dict) and result.get("content"):
        st.success(f"Scenarioresultat\n\n{result.get('content')}")
    else:
        st.info("Ingen scenarioresultat registrert ennå.")

    if feedback and isinstance(feedback, dict) and feedback.get("content"):
        st.warning(f"Tilbakemelding\n\n{feedback.get('content')}")

    st.divider()
    st.markdown(
        "<div style='font-weight:800; font-size:1.1rem; color:#0f172a; margin: 0.3rem 0'>Hva vil du gjøre videre?</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Til start", icon=":material/home:", use_container_width=True):
                reset_to_start(defaults)
                st.rerun()
        with c2:
            if st.button(
                "Se chat-logg", icon=":material/chat:", use_container_width=True
            ):
                st.session_state.page = "chat"
                st.rerun()

        if st.button(
            "Prøv på nytt (samme innstillinger)",
            icon=":material/replay:",
            use_container_width=True,
        ):
            restart_chat()
            st.rerun()
