import time

# Tuning constants
CONTEXT_MESSAGES = 24
MAX_TURNS = 6
# Minimum perceived typing duration for UI polish
MIN_STREAM_TIME_SEC = 0.8

# UI theme constants (aligned to palette #0fa3b1, #b5e2fa, #f9f7f3, #eddea4, #f7a072)
PERSONA_THEME = {
    "Kunde": {"color": "#f7a072", "avatar": "😠", "label": "Kunde"},
    "Student": {"color": "#0fa3b1", "avatar": "🎓", "label": "Student"},
    "Kollega": {"color": "#eddea4", "avatar": "👩‍🍳", "label": "Kollega"},
    "Bystander": {"color": "#b5e2fa", "avatar": "👀", "label": "Forbipasserende"},
    "Ditt svar": {"color": "#0fa3b1", "avatar": "🫵", "label": "Ditt svar"},
    "_you": {"color": "#0fa3b1", "avatar": "🧑‍🍳", "label": "Deg"},
    "Scene": {"color": "#eddea4", "avatar": "🎬", "label": "Scene"},
    "Forteller": {"color": "#eddea4", "avatar": "🎬", "label": "Forteller"},
    "Scenario-resultat": {"color": "#0fa3b1", "avatar": "✅", "label": "Scenario-resultat"},
    "Scenarioresultat": {"color": "#0fa3b1", "avatar": "✅", "label": "Scenarioresultat"},
    "Tilbakemelding": {"color": "#f7a072", "avatar": "💡", "label": "Tilbakemelding"},
    "_default": {"color": "#0fa3b1", "avatar": "🤖", "label": "Agent"},
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
