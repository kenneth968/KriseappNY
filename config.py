import time

# Prompt asset and models
PROMPT_ID = "pmpt_68b54d197a30819485e9f188f780590a0e13554597870097"
MODEL_PRIMARY = "gpt-4o-mini"  # fast mini model
MODEL_FALLBACK = "o3-mini"      # supports reasoning params if needed

# Tuning constants
CONTEXT_MESSAGES = 24
MAX_TURNS = 6
# Make streaming snappy
STREAM_DELAY_SEC = 0.0
MIN_STREAM_TIME_SEC = 0.8

# UI theme constants
PERSONA_THEME = {
    "Kunde": {"color": "#d84a4a", "avatar": "😠"},
    "Student": {"color": "#3b82f6", "avatar": "🎓"},
    "Kollega": {"color": "#16a34a", "avatar": "👩‍🍳"},
    "Bystander": {"color": "#a855f7", "avatar": "👀"},
    "Ditt svar": {"color": "#111827", "avatar": "🫵"},
    "_you": {"color": "#0ea5e9", "avatar": "🧑‍🍳"},
    "Scene": {"color": "#0ea5e9", "avatar": "🎬"},
    "Forteller": {"color": "#0ea5e9", "avatar": "🎬"},
    "Scenario-resultat": {"color": "#10b981", "avatar": "✅"},
    "Scenarioresultat": {"color": "#10b981", "avatar": "✅"},
    "Tilbakemelding": {"color": "#f59e0b", "avatar": "💡"},
    "_default": {"color": "#6b7280", "avatar": "🤖"},
}

ROLE_TO_FALLBACK_NAME = {
    "customer": "Kunde",
    "student": "Student",
    "employee": "Kollega",
    "bystander": "Bystander",
    "user": "Ditt svar",
    "system": "Scene",
}
