import streamlit as st
from state import reset_to_start, restart_chat
from ui_components import page_header, chip


def show(defaults: dict):
    page_header("Kriseøvelse – Feedback")
    meta = st.session_state.get("last_meta", {}) or {}
    turns = st.session_state.get("turns", 0)
    diff = st.session_state.get("difficulty", "")

    chip("Runder brukt", str(turns))
    chip("Vanskelighetsgrad", str(diff))

    result = meta.get("scenarioresultat")
    feedback = meta.get("tilbakemelding")
    if result and isinstance(result, dict) and result.get("content"):
        st.success(f"Scenarioresultat\n\n{result.get('content')}")
    else:
        st.info("Ingen scenarioresultat registrert ennå.")

    if feedback and isinstance(feedback, dict) and feedback.get("content"):
        st.warning(f"Tilbakemelding\n\n{feedback.get('content')}")

    st.divider()
    st.subheader("Hva vil du gjøre videre?")

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
