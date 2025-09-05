import json
from typing import List, Dict

import streamlit as st

from config import CONTEXT_MESSAGES, MAX_TURNS
from model_api import call_model
from ui_components import (
    render_history,
    render_turn_banner,
    page_header,
    progress_turns,
    render_chat_message,
    stream_chat_message,
)
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
    return (
        ("Scenario-resultat" in names)
        or ("Scenarioresultat" in names)
        or ("Tilbakemelding" in names)
    )


def show(defaults: dict):
    page_header(
        "Kriseøvelse – Chat",
        badges={
            "Navn": st.session_state.get("user_name", ""),
            "Vanskelighetsgrad": st.session_state.get("difficulty", ""),
        },
    )

    with st.container():
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Til start", icon=":material/home:", use_container_width=True):
                st.session_state.page = "start"
                st.rerun()
        with c2:
            if st.button(
                "Nullstill", icon=":material/restart_alt:", use_container_width=True
            ):
                reset_to_start(defaults)
                st.rerun()

    if st.session_state.get("ended"):
        with st.container():
            st.success("Scenarioet er ferdig!")
            if st.button(
                "Se tilbakemelding",
                type="primary",
                icon=":material/feedback:",
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
        initial = call_model(compiled)
        # Stream initial messages
        for m in initial:
            # Stream non-system messages; render system (scene) normally
            if m.get("role") == "system" and m.get("name") in ("Scene", "Forteller"):
                render_chat_message(m["role"], m["name"], m["content"])
            else:
                stream_chat_message(m["role"], m["name"], m["content"])
            st.session_state.history.append(m)
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
            user_msg = {
                "name": st.session_state.user_name or "Ansatt",
                "role": "employee",
                "content": user_text,
            }
            st.session_state.history.append(user_msg)
            # Immediate echo using the unified renderer
            render_chat_message(user_msg["role"], user_msg["name"], user_msg["content"])

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
            ai_messages = call_model(compiled)
            # Stream AI messages as they arrive
            for m in ai_messages:
                if m.get("role") == "system" and m.get("name") in ("Scenario-resultat", "Scenarioresultat", "Tilbakemelding"):
                    render_chat_message(m["role"], m["name"], m["content"])
                else:
                    stream_chat_message(m["role"], m["name"], m["content"])
                st.session_state.history.append(m)
            if _check_end(ai_messages) or st.session_state.turns >= MAX_TURNS:
                st.session_state.ended = True
                st.session_state.awaiting_user = False
            else:
                st.session_state.awaiting_user = True
            st.rerun()
