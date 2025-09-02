import streamlit as st
from typing import Dict

from config import PERSONA_THEME, ROLE_TO_FALLBACK_NAME, ROLE_LABEL_NB


def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --c-primary: #0fa3b1; /* teal */
            --c-light: #b5e2fa;   /* light blue */
            --c-cream: #f9f7f3;   /* warm off-white */
            --c-sand: #eddea4;    /* sand */
            --c-peach: #f7a072;   /* peach */
        }
        /* Base layout polish (less top space, avoid pure white) */
        .stApp { background: linear-gradient(180deg, var(--c-light) 0%, var(--c-cream) 32%, var(--c-cream) 100%); }
        .block-container { max-width: 1000px; padding-top: 0.2rem !important; padding-bottom: 1.4rem; }
        header, #MainMenu, footer { visibility: hidden; height: 0 !important; }
        /* Headings */
        .app-title { font-size: 1.6rem; font-weight: 800; color: #0f172a; margin: 0.25rem 0 0.1rem 0; }
        .app-subtitle { color: #334155; margin-bottom: 0.6rem; }
        /* Chips / badges */
        .chip { display:inline-flex; align-items:center; gap:8px; padding:4px 10px; border-radius:14px; font-size:12px; font-weight:600; border:1px solid rgba(0,0,0,0.06); }
        .chip-muted { background: var(--c-sand); color:#0f172a; border-color: rgba(0,0,0,0.06); }
        .chip-primary { background: var(--c-light); color:#075985; border-color: rgba(7,89,133,0.25); }
        /* Turn banner */
        .turn-indicator { 
            display:flex; align-items:center; gap:8px; padding:10px 12px; 
            border-radius:10px; background: var(--c-sand); border:1px solid var(--c-peach); 
            color:#7a3c10; font-weight:600; width:fit-content; margin:6px auto 12px auto; 
            box-shadow: 0 0 0 0 rgba(247,160,114, 0.4);
            animation: pulseGlow 1.6s ease-in-out infinite;
        }
        .turn-dot { width:10px; height:10px; border-radius:50%; background: var(--c-peach); 
            box-shadow: 0 0 0 0 rgba(247,160,114, 0.6); animation: dotPulse 1.6s ease-in-out infinite;
        }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(247,160,114, 0.4);} 70% { box-shadow: 0 0 0 12px rgba(247,160,114, 0);} 100% { box-shadow: 0 0 0 0 rgba(247,160,114, 0);} }
        @keyframes dotPulse { 0% { transform: scale(1);} 50% { transform: scale(1.35);} 100% { transform: scale(1);} }
        .typing-indicator { display:inline-flex; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background: var(--c-cream); color:#374151; border:1px solid var(--c-sand); margin: 4px 0; }
        .typing-dots span { display:inline-block; width:6px; height:6px; margin-right:4px; border-radius:50%; background:#6b7280; animation: blink 1.2s infinite ease-in-out; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
        /* Chat bubbles */
        .bubble { max-width: 780px; padding: 10px 12px; border-radius: 14px; margin: 6px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .bubble-left { background: var(--c-light); border: 1px solid var(--c-primary); }
        .bubble-right { background: var(--c-primary); border: 1px solid var(--c-primary); margin-left: auto; color: #ffffff; }
        .bubble-right .bubble-header { color: #ffffff !important; }
        .bubble-header { font-weight: 600; margin-bottom: 6px; display:flex; align-items:center; gap:8px; }
        .role-badge { font-size: 11px; padding: 2px 6px; border-radius: 8px; background: var(--c-cream); color: #374151; border: 1px solid var(--c-sand); }
        .bubble-content { line-height: 1.5; color: #0f172a; }
        .bubble-right .bubble-content { color: #ffffff; }
        /* Card helpers */
        .callout { border: 1px solid var(--c-sand); background: var(--c-cream); border-radius: 12px; padding: 12px 14px; }
        /* Buttons: ensure strong contrast */
        .stButton > button, button[kind] {
            border-radius: 10px !important;
            border: 1px solid var(--c-primary) !important;
            background: var(--c-cream) !important;
            color: #0f172a !important;
        }
        .stButton > button:hover { filter: brightness(0.96); }
        [data-testid="baseButton-secondary"] { background: var(--c-cream) !important; color: #0f172a !important; border: 1px solid var(--c-primary) !important; }
        [data-testid="baseButton-primary"], .stButton > button[kind="primary"] {
            background: var(--c-primary) !important; color: #ffffff !important; border-color: var(--c-primary) !important;
        }
        [data-testid="baseButton-primary"]:hover, .stButton > button[kind="primary"]:hover { filter: brightness(0.95); }
        /* Inputs / textareas */
        input, textarea { color: #0f172a !important; }
        ::placeholder { color: var(--c-primary) !important; opacity: 1; }
        /* Labels */
        [data-testid="stWidgetLabel"] p { color: #0f172a !important; font-weight: 700; }
        /* Text input backgrounds & borders */
        [data-testid="stTextInputRootElement"] input { background: #ffffff !important; border: 1px solid var(--c-primary) !important; border-radius: 10px !important; }
        /* Slider and radio theming (best-effort) */
        [data-testid="stSlider"] [role="slider"] { background: var(--c-primary) !important; border: 2px solid var(--c-primary) !important; }
        [data-testid="stSlider"] .st-bz, [data-testid="stSlider"] .st-c0, [data-testid="stSlider"] .st-c1 { background: var(--c-primary) !important; }
        [data-testid="stRadio"] label { background: var(--c-cream); color: #0f172a; border: 1px solid var(--c-primary); padding: 6px 10px; border-radius: 12px; margin-right: 6px; }
        /* Progress bar */
        [data-testid="stProgressBar"] p { color: #0f172a !important; font-weight: 700; }
        [data-testid="stProgressBar"] div > div { background-color: var(--c-primary) !important; }
        /* Headings contrast */
        h1, h2, h3 { color: #0f172a !important; }
        /* Chat input container */
        div[contenteditable="true"], textarea { background: #ffffff !important; }
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
