import json
from typing import List, Dict

import streamlit as st

from config import CONTEXT_MESSAGES, MAX_TURNS
from model_api import call_model
from ui_components import render_history, render_turn_banner, page_header, progress_turns
from config import PERSONA_THEME
from state import reset_to_start


def _build_input(user_text: str) -> str:
    context = st.session_state.history[-CONTEXT_MESSAGES:]
    history_json = json.dumps(context, ensure_ascii=False)
    user_name = st.session_state.get("user_name", "Ansatt")
    difficulty = st.session_state.get("difficulty", "")
    if context:
        return (
            "Historikk (JSON-liste av meldinger med name/role/content):\n"
            f"{history_json}\n\n"
            f"Bruker: {user_name} | Runde: {st.session_state.turns}/{MAX_TURNS} | Vanskelighetsgrad: {difficulty}. "
            "Ikke inkluder brukerens melding i output; kun system og andre aktører.\n"
            f"Brukerens siste svar: {user_text.strip() or 'Start scenen.'}"
        )
    return f"Bruker: {user_name} | Runde: 0/{MAX_TURNS} | Vanskelighetsgrad: {difficulty}. Start scenen."


def _check_end(messages: List[Dict]) -> bool:
    meta = st.session_state.get("last_meta")
    if meta and meta.get("scenarioresultat") and meta.get("tilbakemelding"):
        return True
    names = {m.get("name", "") for m in messages}
    return ("Scenario-resultat" in names) or ("Scenarioresultat" in names) or ("Tilbakemelding" in names)


def show(defaults: dict):
    page_header(
        "Kriseøvelse – Chat",
        badges={
            "Navn": st.session_state.get("user_name", ""),
            "Vanskelighetsgrad": st.session_state.get("difficulty", ""),
        },
    )

    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Til start", use_container_width=True):
                st.session_state.page = "start"
                st.rerun()
        with col2:
            if st.button("Nullstill", use_container_width=True):
                reset_to_start(defaults)
                st.rerun()

    st.divider()

    with st.container():
        if st.session_state.get("ended"):
            if st.button(
                "Scenario avsluttet – Trykk her for feedback",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.page = "feedback"
                st.rerun()
        else:
            progress_turns(
                st.session_state.get("turns", 0),
                st.session_state.get("max_turns", MAX_TURNS),
            )

    # Bootstrap initial scene (use typing indicator only)
    if st.session_state.started and not st.session_state.history:
        compiled = _build_input(f"Start scenen for {st.session_state.user_name}.")
        initial = call_model(compiled, stream_placeholder=st.empty())
        st.session_state.history.extend(initial)
        st.session_state.awaiting_user = True
        st.rerun()

    # Render chat (hide meta on chat page)
    render_history(show_meta=False)

    if st.session_state.started and not st.session_state.ended:
        if st.session_state.awaiting_user:
            render_turn_banner()
        placeholder = f"Skriv svaret ditt, {st.session_state.user_name or 'ansatt'}…"
        user_text = st.chat_input(placeholder)
        if user_text:
            st.session_state.awaiting_user = False
            user_msg = {"name": st.session_state.user_name or "Ansatt", "role": "employee", "content": user_text}
            st.session_state.history.append(user_msg)
            # Immediate echo with same bubble style as history (no role label on self)
            with st.chat_message("user", avatar=PERSONA_THEME["_you"]["avatar"]):
                st.markdown(
                    f"<div class='bubble bubble-right'>"
                    f"<div class='bubble-header'>{user_msg['name']}</div>"
                    f"<div class='bubble-content'>{user_msg['content']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Automatic end trigger: user types "end scenario" (or "avslutt scenario")
            if user_text.strip().lower() in ("end scenario", "avslutt scenario"):
                st.session_state.last_meta = {
                    "scenarioresultat": {
                        "name": "Scenarioresultat",
                        "role": "system",
                        "content": "Scenarioet ble avsluttet av brukeren.",
                    },
                    "tilbakemelding": {
                        "name": "Tilbakemelding",
                        "role": "system",
                        "content": "Du avsluttet øvelsen manuelt. Reflekter kort over hva som fungerte og hva du vil forbedre neste gang.",
                    },
                }
                st.session_state.ended = True
                st.session_state.awaiting_user = False
                st.rerun()

            st.session_state.turns += 1
            compiled = _build_input(user_text)
            ai_messages = call_model(compiled, stream_placeholder=st.empty())
            st.session_state.history.extend(ai_messages)
            if _check_end(ai_messages) or st.session_state.turns >= MAX_TURNS:
                st.session_state.ended = True
                st.session_state.awaiting_user = False
            else:
                st.session_state.awaiting_user = True
            st.rerun()
