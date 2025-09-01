import streamlit as st

from state import reset_to_start, restart_chat


def show(defaults: dict):
    st.title("Start Kriseøvelse – Sit Kafe")
    st.session_state["difficulty"] = st.selectbox(
        "Vanskelighetsgrad", ["Lett", "Medium", "Vanskelig"],
        index=["Lett", "Medium", "Vanskelig"].index(st.session_state.get("difficulty", "Medium")),
    )
    st.session_state.user_name = st.text_input("Ditt navn (brukes i scenarioet)", value=st.session_state.user_name)

    col1, col2 = st.columns([1, 1])
    with col1:
        start = st.button("Start scenario", type="primary")
    with col2:
        if st.button("Nullstill"):
            reset_to_start(defaults)
            st.success("Tilbakestilt.")

    if start:
        if not st.session_state.user_name.strip():
            st.warning("Skriv inn navnet ditt før du starter.")
            return
        restart_chat()
        st.rerun()

