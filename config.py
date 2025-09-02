import time

# Tuning constants
CONTEXT_MESSAGES = 24
MAX_TURNS = 6
# Minimum perceived typing duration for UI polish
MIN_STREAM_TIME_SEC = 0.8

# UI theme constants (aligned to palette #0fa3b1, #b5e2fa, #f9f7f3, #eddea4, #f7a072)
PERSONA_THEME = {
    "Kunde": {"color": "#f7a072", "avatar": "😠"},
    "Student": {"color": "#0fa3b1", "avatar": "🎓"},
    "Kollega": {"color": "#eddea4", "avatar": "👩‍🍳"},
    "Bystander": {"color": "#b5e2fa", "avatar": "👀"},
    "Ditt svar": {"color": "#0fa3b1", "avatar": "🫵"},
    "_you": {"color": "#0fa3b1", "avatar": "🧑‍🍳"},
    "Scene": {"color": "#eddea4", "avatar": "🎬"},
    "Forteller": {"color": "#eddea4", "avatar": "🎬"},
    "Scenario-resultat": {"color": "#0fa3b1", "avatar": "✅"},
    "Scenarioresultat": {"color": "#0fa3b1", "avatar": "✅"},
    "Tilbakemelding": {"color": "#f7a072", "avatar": "💡"},
    "_default": {"color": "#0fa3b1", "avatar": "🤖"},
}

ROLE_TO_FALLBACK_NAME = {
    "customer": "Kunde",
    "student": "Student",
    "employee": "Kollega",
    "bystander": "Bystander",
    "user": "Ditt svar",
    "system": "Scene",
}

# Localized, lower-case role labels (Norwegian Bokmål)
ROLE_LABEL_NB = {
    "customer": "kunde",
    "employee": "kollega",
    "student": "student",
    "bystander": "forbipasserende",
    "system": "scene",
    "user": "ditt svar",
}
