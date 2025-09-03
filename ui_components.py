import random
from contextlib import contextmanager
from typing import Dict

import streamlit as st

from config import PERSONA_THEME, ROLE_TO_FALLBACK_NAME, ROLE_LABEL_NB


def _normalize_css(css: str) -> str:
    """Return inline style without surrounding braces."""
    style = css.strip()
    if style.startswith("{") and style.endswith("}"):
        style = style[1:-1]
    return style


@contextmanager
def styled_container(key: str, css: str):
    """Context manager applying inline CSS to a container.

    ``key`` is kept for API compatibility but unused.
    """
    style = _normalize_css(css)
    container = st.container()
    container.markdown(f"<div style=\"{style}\">", unsafe_allow_html=True)
    with container:
        yield container
    container.markdown("</div>", unsafe_allow_html=True)


def external_badge(kind: str, name: str | None = None, url: str | None = None) -> None:
    """Render a simple clickable badge without ``streamlit-extras``."""
    label = name or kind
    href = f' href="{url}" target="_blank"' if url else ""
    st.markdown(
        f"<a{href} style='text-decoration:none;'>"
        f"<span style='display:inline-block;padding:2px 8px;border-radius:10px;"
        f"background:#f1f5f9;color:#334155;font-size:0.8rem;margin-right:4px;'>"
        f"{label}</span></a>",
        unsafe_allow_html=True,
    )


def chip(label: str, value: str) -> None:
    """Render a small inline badge for key-value pairs."""
    style = (
        "display:inline-block;padding:2px 8px;border-radius:10px;"
        "background:#f1f5f9;color:#334155;font-size:0.8rem;margin-right:4px;"
    )
    st.markdown(
        f"<span style='{style}'>{label}: <strong>{value}</strong></span>",
        unsafe_allow_html=True,
    )

def page_header(title: str, subtitle: str = "", badges: Dict[str, str] | None = None) -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"#### {subtitle}")
    if badges:
        for k, v in badges.items():
            chip(k, str(v))


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

    descriptor = None
    if role == "customer":
        lower_disp = display_name.strip().lower()
        if "kunde" in lower_disp:
            descriptor = lower_disp if lower_disp != "kunde" else None
            display_name = ""

    # If the model gave us a generic name like "kunde", replace with a random Norwegian name
    if not is_self and _is_generic_name(display_name, role):
        display_name = _get_or_create_role_random_name(role)

    header_text = display_name if is_self else f"{display_name} ({descriptor or role_label(role)})"

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
