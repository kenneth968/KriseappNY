import streamlit as st
from pathlib import Path
from typing import Dict

from config import PERSONA_THEME, ROLE_TO_FALLBACK_NAME, ROLE_LABEL_NB


def inject_css() -> None:
    """Inject shared app styles."""
    st.markdown(Path("styles.css").read_text(), unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", badges: Dict[str, str] | None = None) -> None:
    st.markdown(f"<div class='app-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='app-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
    if badges:
        chips = " ".join([f"<span class='chip chip-muted'>{k}: <b>{v}</b></span>" for k, v in badges.items()])
        st.markdown(chips, unsafe_allow_html=True)


def progress_turns(turns: int, max_turns: int) -> None:
    pct = 0 if max_turns <= 0 else min(1.0, max(0.0, turns / float(max_turns)))
    st.progress(pct, text=f"Runde {turns} av {max_turns}")


def _role_to_streamlit(role: str, name: str = "", user_name: str = "") -> str:
    if role == "employee" and name and name == user_name:
        return "user"
    if role == "user":
        return "user"
    return "assistant"


def render_history(show_meta: bool = True):
    user_name = st.session_state.get("user_name", "")

    def theme_for(msg: Dict) -> (str, Dict):
        role = msg.get("role", "")
        name = (msg.get("name") or ROLE_TO_FALLBACK_NAME.get(role, "")).strip() or "_default"
        # Map theme by role first to keep colors/icons consistent with actor type
        role_theme_key = {
            "customer": "Kunde",
            "student": "Student",
            "employee": "Kollega",
            "bystander": "Bystander",
            "system": "Scene",
        }.get(role, "_default")
        theme = PERSONA_THEME.get(role_theme_key, PERSONA_THEME["_default"])
        if user_name and name == user_name and role == "employee":
            theme = PERSONA_THEME["_you"]
        return name, theme

    def sanitize_name(display_name: str, role: str) -> str:
        if not display_name:
            return display_name
        # If LLM returns e.g. "Kunde (Trine)", extract the inner name
        import re
        m = re.match(r"^(Kunde|Student|Kollega|Bystander|Scene|Forteller)\s*\(([^)]+)\)$", display_name)
        if m:
            return m.group(2).strip()
        # Remove stray duplicated role labels in name like "Trine (Kunde) (kunde)"
        display_name = re.sub(r"\s*\(kunde\)$", "", display_name, flags=re.IGNORECASE)
        display_name = re.sub(r"\s*\(student\)$", "", display_name, flags=re.IGNORECASE)
        display_name = re.sub(r"\s*\(kollega\)$", "", display_name, flags=re.IGNORECASE)
        display_name = re.sub(r"\s*\(bystander\)$", "", display_name, flags=re.IGNORECASE)
        return display_name

    def render_center_box(kind: str, content: str):
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

    # Render optional meta (hidden on chat page when show_meta=False)
    if show_meta:
        meta = st.session_state.get("last_meta")
        if meta:
            if meta.get("oppdrag"):
                render_center_box("scene", meta.get("oppdrag"))
            if meta.get("sjekkliste"):
                _, mid, _ = st.columns([1, 2, 1])
                with mid:
                    st.markdown("<div style='color:#334155; font-weight:600; margin-top:4px'>Sjekkliste</div>", unsafe_allow_html=True)
                    for item in meta.get("sjekkliste"):
                        st.markdown(f"- {item}")
            if meta.get("scenarioresultat") and isinstance(meta.get("scenarioresultat"), dict):
                content = str(meta["scenarioresultat"].get("content", "")).strip()
                if content:
                    render_center_box("result", content)
            if meta.get("tilbakemelding") and isinstance(meta.get("tilbakemelding"), dict):
                content = str(meta["tilbakemelding"].get("content", "")).strip()
                if content:
                    render_center_box("feedback", content)

    # Title-case display label from mapping (Kunde, Student, Kollega, ...)
    def role_label(role: str) -> str:
        return ROLE_TO_FALLBACK_NAME.get(role, role)

    for msg in st.session_state.history:
        role = msg.get("role", "assistant")
        name, theme = theme_for(msg)
        content = msg.get("content", "")

        if role == "system" and name in ("Scene", "Forteller"):
            render_center_box("scene", content)
            continue

        streamlit_role = _role_to_streamlit(role, name, user_name)
        align_class = "bubble-right" if streamlit_role == "user" else "bubble-left"
        display_name = sanitize_name(name, role)
        is_self = (streamlit_role == "user")
        header_text = display_name if is_self else f"{display_name} ({role_label(role)})"
        with st.chat_message(streamlit_role, avatar=theme["avatar"]):
            st.markdown(
                f"<div class='bubble {align_class}'>"
                f"<div class='bubble-header'>"
                f"{header_text}</div>"
                f"<div class='bubble-content'>{content}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def render_turn_banner():
    st.markdown(
        f"<div class='turn-indicator'><div class='turn-dot'></div>Din tur til å handle, {st.session_state.get('user_name','')}.</div>",
        unsafe_allow_html=True,
    )
