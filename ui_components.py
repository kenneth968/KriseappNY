import streamlit as st
from typing import Dict

from config import PERSONA_THEME, ROLE_TO_FALLBACK_NAME


def inject_css():
    st.markdown(
        """
        <style>
        .turn-indicator { 
            display:flex; align-items:center; gap:8px; padding:10px 12px; 
            border-radius:10px; background:#ecfeff; border:1px solid #67e8f9; 
            color:#0e7490; font-weight:600; width:fit-content; margin:6px auto 12px auto; 
            box-shadow: 0 0 0 0 rgba(14,116,144, 0.6);
            animation: pulseGlow 1.6s ease-in-out infinite;
        }
        .turn-dot { width:10px; height:10px; border-radius:50%; background:#06b6d4; 
            box-shadow: 0 0 0 0 rgba(6,182,212, 0.7); animation: dotPulse 1.6s ease-in-out infinite;
        }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(14,116,144, 0.5);} 70% { box-shadow: 0 0 0 12px rgba(14,116,144, 0);} 100% { box-shadow: 0 0 0 0 rgba(14,116,144, 0);} }
        @keyframes dotPulse { 0% { transform: scale(1);} 50% { transform: scale(1.35);} 100% { transform: scale(1);} }
        .typing-indicator {
            display:inline-flex; align-items:center; gap:8px; padding:8px 10px;
            border-radius:12px; background:#f3f4f6; color:#374151; border:1px solid #e5e7eb;
            margin: 4px 0;
        }
        .typing-dots span {
            display:inline-block; width:6px; height:6px; margin-right:4px; border-radius:50%; background:#6b7280;
            animation: blink 1.2s infinite ease-in-out;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

        /* Chat bubbles */
        .bubble { max-width: 720px; padding: 10px 12px; border-radius: 14px; margin: 6px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .bubble-left { background: #ffffff; border: 1px solid #e5e7eb; }
        .bubble-right { background: #e6f3ff; border: 1px solid #bfdbfe; margin-left: auto; }
        .bubble-header { font-weight: 600; margin-bottom: 6px; display:flex; align-items:center; gap:8px; }
        .role-badge { font-size: 11px; padding: 2px 6px; border-radius: 8px; background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
        .bubble-content { line-height: 1.45; color: #111827; }
        </style>
        """,
        unsafe_allow_html=True,
    )


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

    # Localized, lower-case role label for header parentheses
    def localized_role(role: str) -> str:
        return {
            "customer": "kunde",
            "employee": "kollega",
            "student": "student",
            "bystander": "forbipasserende",
            "system": "scene",
            "user": "ditt svar",
        }.get(role, role)

    for msg in st.session_state.history:
        role = msg.get("role", "assistant")
        name, theme = theme_for(msg)
        content = msg.get("content", "")

        if role == "system" and name in ("Scene", "Forteller"):
            render_center_box("scene", content)
            continue

        streamlit_role = _role_to_streamlit(role, name, user_name)
        align_class = "bubble-right" if streamlit_role == "user" else "bubble-left"
        role_text = localized_role(role)
        header_text = f"{name} ({role_text})" if role_text else name
        with st.chat_message(streamlit_role, avatar=theme["avatar"]):
            st.markdown(
                f"<div class='bubble {align_class}'>"
                f"<div class='bubble-header' style='color:{theme['color']}'>"
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
