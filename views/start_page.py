import streamlit as st

from state import reset_to_start, restart_chat
from ui_components import page_header


def show(defaults: dict):
    page_header(
        "Kriseøvelse – Sit Kafe",
        "Tren på å håndtere krevende kundedialoger i et trygt miljø.",
    )

    with st.form("start-form", clear_on_submit=False):
        c1, c2 = st.columns([1, 1])
        with c1:
            st.session_state.user_name = st.text_input(
                "Ditt navn",
                value=st.session_state.user_name,
                placeholder="Skriv inn navnet ditt",
            )
        with c2:
            # Difficulty control (keep select_slider but themed via CSS; label contrast improved)
            st.session_state["difficulty"] = st.select_slider(
                "Vanskelighetsgrad",
                options=["Lett", "Medium", "Vanskelig"],
                value=st.session_state.get("difficulty", "Medium"),
            )

        st.markdown(
            "<div class='callout' style='color:#0f172a; margin-top:6px'>Du kan endre innstillingene senere. Navnet brukes i dialogen.</div>",
            unsafe_allow_html=True,
        )

        b1, b2 = st.columns([1, 1])
        with b1:
            start = st.form_submit_button("Start scenario", type="primary", use_container_width=True)
        with b2:
            reset = st.form_submit_button("Nullstill", use_container_width=True)

    if 'reset' in locals() and reset:
        reset_to_start(defaults)
        st.success("Tilbakestilt.")

    if 'start' in locals() and start:
        if not (st.session_state.user_name or "").strip():
            st.warning("Skriv inn navnet ditt før du starter.")
            return
        restart_chat()
        st.rerun()
