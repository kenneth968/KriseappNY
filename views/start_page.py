import streamlit as st

from state import reset_to_start, restart_chat
from ui_components import page_header, styled_container, external_badge

BLOCK_STYLE = """
    {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: rgba(49, 51, 63, 0.05);
    }
"""


def show(defaults: dict):
    page_header(
        "Kriseøvelse – Sit Kafe",
        "Tren på å håndtere krevende kundedialoger i et trygt miljø.",
    )
    external_badge("streamlit", url="https://streamlit.io")

    with st.form("start-form", clear_on_submit=False):
        with styled_container(key="name_difficulty", css=BLOCK_STYLE):
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

            st.status(
                "Du kan endre innstillingene senere. Navnet brukes i dialogen.",
                state="complete",
                expanded=False,
            )

        # Optional: allow users to provide their own OpenAI API key
        with styled_container(key="api_key_block", css=BLOCK_STYLE):
            st.session_state.api_key = st.text_input(
                "OpenAI API-nøkkel (valgfritt)",
                value=st.session_state.get("api_key", ""),
                type="password",
                placeholder="sk-...",
                help=(
                    "Bruk din egen nøkkel hvis appen kjører på Community Cloud. "
                    "Nøkkelen lagres kun i denne økten."
                ),
            )

        st.divider()

        with st.container():
            b1, b2 = st.columns([1, 1])
            with b1:
                start = st.form_submit_button(
                    "Start scenario",
                    type="primary",
                    use_container_width=True,
                    icon=":material/play_arrow:",
                )
            with b2:
                reset = st.form_submit_button(
                    "Nullstill",
                    use_container_width=True,
                    icon=":material/restart_alt:",
                )

    if "reset" in locals() and reset:
        reset_to_start(defaults)
        st.success("Tilbakestilt.")

    if "start" in locals() and start:
        if not (st.session_state.user_name or "").strip():
            st.warning("Skriv inn navnet ditt før du starter.")
            return
        restart_chat()
        st.rerun()
