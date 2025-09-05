import os
import streamlit as st

from state import reset_to_start, restart_chat
from ui_components import page_header


def show(defaults: dict):
    # Prefer Streamlit Secrets on Community Cloud, fallback to env vars locally
    auth_pw = (st.secrets.get("AUTH_PASSWORD") if hasattr(st, "secrets") else None) or os.getenv("AUTH_PASSWORD", "")
    server_key_present = bool(
        ((st.secrets.get("OPENAI_API_KEY") or st.secrets.get("SERVER_OPENAI_API_KEY")) if hasattr(st, "secrets") else None)
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("SERVER_OPENAI_API_KEY")
    )

    page_header(
        "Kriseøvelse – Sit Kafe",
        "Tren på å håndtere krevende kundedialoger i et trygt miljø.",
    )

    with st.form("start-form", clear_on_submit=False):
        with st.container():
            c1, c2 = st.columns([1, 1])
            with c1:
                st.session_state.user_name = st.text_input(
                    "Ditt navn",
                    value=st.session_state.user_name,
                    placeholder="Skriv inn navnet ditt",
                )
            with c2:
                st.session_state["difficulty"] = st.select_slider(
                    "Vanskelighetsgrad",
                    options=["Lett", "Medium", "Vanskelig"],
                    value=st.session_state.get("difficulty", "Medium"),
                )

            st.info("Du kan endre innstillingene senere. Navnet brukes i dialogen.")

        # Optional password gate controlled by AUTH_PASSWORD env var
        entered_pw = ""
        if auth_pw:
            entered_pw = st.text_input(
                "Tilgangspassord",
                type="password",
                help="Be eier om passord dersom du ikke har ett.",
            )

        # Optional: allow users to provide their own OpenAI API key (hidden if server key is configured)
        if not server_key_present:
            with st.container():
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
        # Enforce password if configured
        if auth_pw and not st.session_state.get("authenticated"):
            if entered_pw != auth_pw:
                st.warning("Feil passord. Prøv igjen.")
                return
            st.session_state.authenticated = True
        if not (st.session_state.user_name or "").strip():
            st.warning("Skriv inn navnet ditt før du starter.")
            return
        restart_chat()
        st.rerun()

