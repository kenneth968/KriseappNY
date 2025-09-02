# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Streamlit entrypoint and simple router.
- `views/`: UI pages (`start_page.py`, `chat_page.py`, `feedback_page.py`) exposing `show(defaults)`.
- `model_api.py`: Orchestrates the agents workflow (`agents.Agent`, `agents.Runner`) and Pydantic schemas.
- `ui_components.py`: Shared CSS injection and chat/message renderers.
- `state.py`: Session state helpers (defaults, resets, restarts).
- `config.py`: Tunables (models, limits, UI theme mapping).
  

## Build, Test, and Development Commands
- Activate venv (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Run app: `streamlit run app.py` (or `python -m streamlit run app.py`)
- Install deps (if missing): `pip install streamlit pydantic`
- Optional formatting/lint: `black .` and `ruff .` if you use them.

## Coding Style & Naming Conventions
- Python 3.10+, 4‑space indentation, type hints where practical.
- Files/functions: `lower_snake_case`; Pydantic models: `UpperCamelCase`.
- Views follow `*_page.py` with a single `show(defaults: dict)` entry.
- Keep UI in `views/` and logic/state in `model_api.py`, `state.py`, `ui_components.py`.

## Testing Guidelines
- No tests yet. Prefer `pytest` for new tests.
- Name tests `test_*.py` mirroring modules; place beside source or in `tests/`.
- Run locally: `pytest -q` (add `pytest` to your environment first).

## Commit & Pull Request Guidelines
- Commits: imperative and scoped. Conventional Commits encouraged (e.g., `feat: add end monitor`).
- PRs: include a concise description, linked issue, validation steps (`streamlit run app.py`), and UI screenshots where relevant.
- Keep PRs small and focused; note any config changes in `config.py`.

## Security & Configuration Tips
- Do not commit secrets. Use environment variables (e.g., `os.getenv`) for keys.
- Keep model IDs and tunables in `config.py`; avoid hardcoding in views.
- `.venv/` stays untracked; avoid committing cache or local data.

## Agent‑Specific Notes
- To add a persona: define an `Agent` and register it in `scenario_agent.handoffs` (in `model_api.py`).
- Keep `role` values aligned with `ROLE_TO_FALLBACK_NAME` in `config.py` to ensure correct theming and rendering.
