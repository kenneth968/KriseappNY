import random
from typing import Dict

import streamlit as st

from config import PERSONA_THEME, ROLE_TO_FALLBACK_NAME, ROLE_LABEL_NB


def inject_css():
    # Minimal CSS for pulsing turn indicator and typing dots.
    st.markdown(
        """
        <style>
        .typing-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 10px;
            background: #f9f7f3; /* off-white */
            border: 1px solid #b5e2fa; /* light blue */
            color: #334155; /* slate */
            font-weight: 600;
            width: fit-content;
            margin: 6px auto 8px auto;
        }
        .typing-dots { display: inline-flex; gap: 3px; }
        .typing-dots span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #334155;
            display: inline-block;
            animation: typingBlink 1.2s ease-in-out infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: .2s; }
        .typing-dots span:nth-child(3) { animation-delay: .4s; }
        @keyframes typingBlink {
            0% { opacity: .2; transform: translateY(0); }
            50% { opacity: 1; transform: translateY(-2px); }
            100% { opacity: .2; transform: translateY(0); }
        }
        .turn-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 12px;
            border-radius: 10px;
            background: #eddea4; /* sand */
            border: 1px solid #f7a072; /* peach */
            color: #7a3c10; /* dark brown text for contrast */
            font-weight: 600;
            width: fit-content;
            margin: 6px auto 12px auto;
            box-shadow: 0 0 0 0 rgba(247,160,114, 0.4);
            animation: pulseGlow 1.6s ease-in-out infinite;
        }
        .turn-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #f7a072; /* peach */
            box-shadow: 0 0 0 0 rgba(247,160,114, 0.6);
            animation: dotPulse 1.6s ease-in-out infinite;
        }
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 0 rgba(247,160,114, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(247,160,114, 0); }
            100% { box-shadow: 0 0 0 0 rgba(247,160,114, 0); }
        }
        @keyframes dotPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.35); }
            100% { transform: scale(1); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def page_header(title: str, subtitle: str = "", badges: Dict[str, str] | None = None) -> None:
    st.markdown(f"<div class='app-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='app-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
    if badges:
        chips = " ".join([f"<span class='chip chip-muted'>{k}: <b>{v}</b></span>" for k, v in badges.items()])
        st.markdown(chips, unsafe_allow_html=True)


def chip(label: str, value: str) -> None:
    """Render a small inline badge for key-value pairs.

    Kept minimal and self-contained so it works even if themed CSS is missing.
    """
    style = (
        "display:inline-block;padding:2px 8px;border-radius:10px;"
        "background:#f1f5f9;color:#334155;font-size:0.8rem;margin-right:6px;"
    )
    st.markdown(
        f"<span class='chip chip-muted' style='{style}'>{label}: <b>{value}</b></span>",
        unsafe_allow_html=True,
    )


def progress_turns(turns: int, max_turns: int) -> None:
    pct = 0 if max_turns <= 0 else min(1.0, max(0.0, turns / float(max_turns)))
    st.progress(pct, text=f"Runde {turns} av {max_turns}")


def _role_to_streamlit(role: str, name: str = "", user_name: str = "") -> str:
    if role == "employee" and name and name == user_name:
        return "user"
    if role == "user":
        return "user"
    return "assistant"
def role_label(role: str) -> str:
    # Prefer localized, lowercase labels for parentheses, e.g., (kunde)
    return ROLE_LABEL_NB.get(role, role)


def sanitize_name(display_name: str, role: str) -> str:
    if not display_name:
        return display_name
    import re

    m = re.match(r"^(Kunde|Student|Kollega|Bystander|Scene|Forteller)\s*\(([^)]+)\)$", display_name)
    if m:
        return m.group(2).strip()
    display_name = re.sub(r"\s*\(kunde\)$", "", display_name, flags=re.IGNORECASE)
    display_name = re.sub(r"\s*\(student\)$", "", display_name, flags=re.IGNORECASE)
    display_name = re.sub(r"\s*\(kollega\)$", "", display_name, flags=re.IGNORECASE)
    display_name = re.sub(r"\s*\(bystander\)$", "", display_name, flags=re.IGNORECASE)
    return display_name


# Simple Norwegian name pool used when models return generic role names
_NB_NAMES = [
    "Kari", "Nora", "Anders", "Lars", "Ola", "Knut", "Mari", "Anne",
    "Ingrid", "Hanne", "Sigrid", "Eirik", "Per", "Kjetil", "Morten",
    "Jon", "Silje", "Hilde", "Trine", "Camilla",
]


def _get_or_create_role_random_name(role: str) -> str:
    key = "_rand_name_" + (role or "")
    if key not in st.session_state:
        st.session_state[key] = random.choice(_NB_NAMES)
    return st.session_state[key]


def _is_generic_name(name: str, role: str) -> bool:
    if not name:
        return True
    n = str(name).strip().lower()
    generic = {
        "kunde", "customer", "kollega", "employee", "medarbeider", "bystander",
        "forbipasserende", "student", "scene", "forteller", "system", "user",
        "ditt svar", "ansatt",
    }
    fallback = ROLE_TO_FALLBACK_NAME.get(role, "").strip().lower()
    if role == "customer" and "kunde" in n:
        return True
    return n in generic or (fallback and n == fallback.lower())


def render_center_box(kind: str, content: str) -> None:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if kind == "scene":
            st.info(content)
        elif kind == "result":
            st.success(content)
        elif kind == "feedback":
            st.warning(content)
        else:
            st.info(content)


def render_chat_message(role: str, name: str, content: str) -> None:
    user_name = st.session_state.get("user_name", "")
    persona_name = (name or ROLE_TO_FALLBACK_NAME.get(role, "")).strip() or "_default"
    role_theme_key = {
        "customer": "Kunde",
        "student": "Student",
        "employee": "Kollega",
        "bystander": "Bystander",
        "system": "Scene",
    }.get(role, "_default")
    theme = PERSONA_THEME.get(role_theme_key, PERSONA_THEME["_default"])
    if user_name and persona_name == user_name and role == "employee":
        theme = PERSONA_THEME["_you"]

    display_name = sanitize_name(persona_name, role)

    if role == "system" and persona_name in ("Scene", "Forteller"):
        render_center_box("scene", content)
        return
    if role == "system" and persona_name in ("Scenario-resultat", "Scenarioresultat"):
        render_center_box("result", content)
        return
    if role == "system" and persona_name == "Tilbakemelding":
        render_center_box("feedback", content)
        return

    streamlit_role = _role_to_streamlit(role, persona_name, user_name)
    is_self = streamlit_role == "user"

    # Stabilize persona names across the session to avoid mid-run renaming.
    if not is_self:
        fixed_key = f"_fixed_name_{role}"
        fixed = st.session_state.get(fixed_key)
        if fixed:
            display_name = fixed
        else:
            if _is_generic_name(display_name, role):
                display_name = _get_or_create_role_random_name(role)
            # Persist the first seen non-generic or chosen fallback as the fixed name
            st.session_state[fixed_key] = display_name
    header_text = display_name if is_self else f"{display_name} ({role_label(role)})"

    with st.chat_message(streamlit_role, avatar=theme["avatar"]):
        # Use Streamlit's default theme colors for readability
        st.markdown(f"**{header_text}**")
        st.markdown(content)


def render_history(show_meta: bool = True) -> None:
    if show_meta:
        meta = st.session_state.get("last_meta")
        if meta:
            if meta.get("oppdrag"):
                render_center_box("scene", meta.get("oppdrag"))
            if meta.get("sjekkliste"):
                _, mid, _ = st.columns([1, 2, 1])
                with mid:
                    st.markdown(
                        "<p style='color:#334155;font-weight:600;margin-top:4px;'>Sjekkliste</p>",
                        unsafe_allow_html=True,
                    )
                    for item in meta.get("sjekkliste"):
                        st.markdown(f"- {item}")
            if meta.get("scenarioresultat") and isinstance(meta.get("scenarioresultat"), dict):
                m = meta["scenarioresultat"]
                render_chat_message(m.get("role", "system"), m.get("name", "Scenarioresultat"), str(m.get("content", "")))
            if meta.get("tilbakemelding") and isinstance(meta.get("tilbakemelding"), dict):
                m = meta["tilbakemelding"]
                render_chat_message(m.get("role", "system"), m.get("name", "Tilbakemelding"), str(m.get("content", "")))

    for msg in st.session_state.history:
        render_chat_message(
            msg.get("role", ""),
            msg.get("name", ""),
            msg.get("content", ""),
        )
def render_turn_banner() -> None:
    """Display a banner indicating the user's turn."""
    st.markdown(
        """
        <style>
        .turn-banner {
            display:flex;
            align-items:center;
            gap:8px;
            padding:10px 12px;
            border-radius:10px;
            background:#eddea4;
            border:1px solid #f7a072;
            color:#7a3c10;
            font-weight:600;
            width:fit-content;
            margin:6px auto 12px auto;
            box-shadow:0 0 0 0 rgba(247,160,114,0.4);
            animation:pulseGlow 1.6s ease-in-out infinite;
        }
        .turn-banner .dot {
            width:10px;
            height:10px;
            border-radius:50%;
            background:#f7a072;
            box-shadow:0 0 0 0 rgba(247,160,114,0.6);
            animation:dotPulse 1.6s ease-in-out infinite;
        }
        @keyframes pulseGlow {
            0% { box-shadow:0 0 0 0 rgba(247,160,114,0.4); }
            70% { box-shadow:0 0 0 12px rgba(247,160,114,0); }
            100% { box-shadow:0 0 0 0 rgba(247,160,114,0); }
        }
        @keyframes dotPulse {
            0% { transform:scale(1); }
            50% { transform:scale(1.35); }
            100% { transform:scale(1); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='turn-banner'><span class='dot'></span>Din tur</div>",
        unsafe_allow_html=True,
    )
