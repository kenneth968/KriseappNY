import importlib


def test_config_constants_and_mappings():
    config = importlib.import_module("config")

    assert isinstance(config.CONTEXT_MESSAGES, int)
    assert isinstance(config.MAX_TURNS, int)

    assert isinstance(config.PERSONA_THEME, dict)
    assert "Kunde" in config.PERSONA_THEME
    # Each theme entry has color and avatar
    for theme in config.PERSONA_THEME.values():
        assert "color" in theme and "avatar" in theme

    assert isinstance(config.ROLE_TO_FALLBACK_NAME, dict)
    for role in ["customer", "student", "employee", "bystander", "user", "system"]:
        assert role in config.ROLE_TO_FALLBACK_NAME

    # Localized labels present
    assert hasattr(config, "ROLE_LABEL_NB")
    for role in ["customer", "student", "employee", "bystander", "user", "system"]:
        assert role in config.ROLE_LABEL_NB
