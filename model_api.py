import json
import time
from typing import List, Dict, Optional, Literal

import streamlit as st
from pydantic import BaseModel, Field

from config import MIN_STREAM_TIME_SEC
from async_utils import run_async

# Agents framework
from agents import Agent, Runner
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


class Oppdrag(BaseModel):
    beskrivelse: Optional[str] = Field(default=None, description="Kort oppsummering (maks fire setninger)")


class ScenarioMessage(BaseModel):
    name: str
    role: Literal["system", "customer", "employee", "student", "bystander"]
    content: str


class ScenarioResult(BaseModel):
    name: Literal["Scenarioresultat"]
    role: Literal["system"]
    content: str


class ScenarioFeedback(BaseModel):
    name: Literal["Tilbakemelding"]
    role: Literal["system"]
    content: str


class ScenarioOutput(BaseModel):
    oppdrag: Optional[Oppdrag] = None
    sjekkliste: Optional[List[str]] = None
    meldinger: List[ScenarioMessage]
    scenarioresultat: Optional[ScenarioResult] = None
    tilbakemelding: Optional[ScenarioFeedback] = None


# Persona agents (configurable, available for handoff)
scene_agent = Agent(
    name="Scene Agent",
    handoff_description="Genererer første 'Scene'-melding",
    instructions=prompt_with_handoff_instructions(
        "Du skriver kun ett meldingsobjekt: {name: 'Scene', role: 'system', content: <maks fire setninger>}. "
        "Beskriv hendelsen på Sit Kafe med autentiske detaljer. Skriv på norsk."
    ),
)

customer_agent = Agent(
    name="Kunde Agent",
    handoff_description="Skriver realistisk sint kundereplikk",
    instructions=prompt_with_handoff_instructions(
        "Du skriver kun ett meldingsobjekt for en kunde med role 'customer'. "
        "Sett 'name' til et realistisk norsk fornavn (f.eks. Kari, Anders, Nora). "
        "Vær konkret, kort (maks fire setninger) og på norsk. Hold deg til situasjonen."
    ),
)

bystander_agent = Agent(
    name="Forbipasserende Agent",
    handoff_description="Legger til sjeldne kommenterer fra forbipasserende",
    instructions=prompt_with_handoff_instructions(
        "Du skriver kun ett meldingsobjekt for en forbipasserende (role 'bystander'). Sett 'name' til et realistisk norsk fornavn. "
        "Bruk maks fire setninger. Bare når vanskelighetsgrad krever det."
    ),
)

colleague_agent = Agent(
    name="Kollega Agent",
    handoff_description="Gir støtte fra en kollega ved behov",
    instructions=prompt_with_handoff_instructions(
        "Du skriver kun ett meldingsobjekt for en kollega (role 'employee'). Sett 'name' til et realistisk norsk fornavn. "
        "Bruk maks fire setninger. Bare ved mellom/vanskelig."
    ),
)


# Director agent composes the structured output
scenario_agent = Agent(
    name="Scenarioleder",
    instructions=prompt_with_handoff_instructions(
        "Du er scenarieleder for en kriseøvelse ved Sit Kafe. Alt på norsk. "
        "Produser et strukturert resultat med feltene oppdrag (valgfritt), sjekkliste (valgfritt), meldinger (liste), "
        "scenarioresultat (valgfritt) og tilbakemelding (valgfritt). Følg disse reglene:\n"
        "- Første tur (turn_count == 0): returner kun to meldinger i rekkefølge: Scene (system) og en sint kunde (customer).\n"
        "- Etter første tur: fortsett dialog mellom kunden og den ansatte. Hvis difficulty er 'Medium' eller 'Vanskelig', "
        "  inkluder av og til en forbipasserende (bystander) eller kollega (employee) med realistisk norsk navn.\n"
        "- Maks fire setninger per melding. Respekter vanskelighetsgrad og brukers navn fra konteksten.\n"
        "- Maks seks runder totalt; ved avslutning fyll inn 'scenarioresultat' og 'tilbakemelding'.\n"
        "- Du kan delegere via handoffs til Scene Agent / Kunde Agent / Forbipasserende Agent / Kollega Agent for å komponere meldinger."
    ),
    handoffs=[scene_agent, customer_agent, bystander_agent, colleague_agent],
    output_type=ScenarioOutput,
)


class EndDecision(BaseModel):
    should_end: bool
    result: Optional[str] = None
    feedback: Optional[str] = None


end_monitor_agent = Agent(
    name="Avslutningsvakt",
    handoff_description="Overvåker om scenariet skal avsluttes",
    instructions=(
        "Analyser siste meldinger, vanskelighetsgrad og turn_count. Hvis turn_count >= 6, eller konflikten er løst/feilet, "
        "returner should_end=true og fyll ut 'result' (1–2 setninger, norsk) og 'feedback' (1–3 setninger, norsk). "
        "Ellers should_end=false."
    ),
    output_type=EndDecision,
)


def call_model(compiled_input: str, stream_placeholder: Optional[object] = None) -> List[Dict]:
    # Show typing indicator right away
    start_time = time.time()
    if stream_placeholder is not None:
        stream_placeholder.markdown(
            "<div class='typing-indicator'><div class='typing-dots'>"
            "<span></span><span></span><span></span></div>Genererer svar …</div>",
            unsafe_allow_html=True,
        )

    async def _run():
        ctx = {
            "difficulty": str(st.session_state.get("difficulty", "")),
            "user_name": str(st.session_state.get("user_name", "")),
            "turn_count": str(st.session_state.get("turns", 0)),
            "max_turns": str(st.session_state.get("max_turns", 6)),
        }
        result = await Runner.run(scenario_agent, compiled_input, context=ctx)
        return result.final_output

    raw_out = run_async(_run())

    # Robustly coerce the agent output into ScenarioOutput
    def _coerce_output(val) -> ScenarioOutput:
        try:
            if isinstance(val, ScenarioOutput):
                return val
            if isinstance(val, dict):
                return ScenarioOutput(**val)
            if isinstance(val, str):
                try:
                    data = json.loads(val)
                    if isinstance(data, dict):
                        return ScenarioOutput(**data)
                except Exception:
                    pass
            # Fallback: wrap plain text into a minimal structured object
            is_initial_local = (
                st.session_state.get("turns", 0) == 0
                and len(st.session_state.get("history", [])) == 0
            )
            msg_role = "system" if is_initial_local else "customer"
            msg_name = "Scene" if is_initial_local else "Kunde"
            content = str(val)
            return ScenarioOutput(
                oppdrag=None,
                sjekkliste=[],
                meldinger=[
                    ScenarioMessage(name=msg_name, role=msg_role, content=content)
                ],
                scenarioresultat=None,
                tilbakemelding=None,
            )
        except Exception:
            # Final fallback: empty conversation step
            return ScenarioOutput(
                oppdrag=None,
                sjekkliste=[],
                meldinger=[],
                scenarioresultat=None,
                tilbakemelding=None,
            )

    out: ScenarioOutput = _coerce_output(raw_out)

    # Minimum indicator time for perceived streaming feel
    elapsed = time.time() - start_time
    if stream_placeholder is not None and elapsed < MIN_STREAM_TIME_SEC:
        time.sleep(MIN_STREAM_TIME_SEC - elapsed)

    # Build cleaned messages and optional meta
    cleaned: List[Dict] = []
    is_initial = (st.session_state.get("turns", 0) == 0 and len(st.session_state.get("history", [])) == 0)

    # Save meta except on initial turn (keeps first turn minimal)
    if not is_initial:
        st.session_state.last_meta = {
            "oppdrag": (out.oppdrag.beskrivelse if out.oppdrag else None),
            "sjekkliste": out.sjekkliste or [],
            "scenarioresultat": (out.scenarioresultat.dict() if out.scenarioresultat else None),
            "tilbakemelding": (out.tilbakemelding.dict() if out.tilbakemelding else None),
        }
    else:
        st.session_state.last_meta = {}

    messages = out.meldinger or []
    if is_initial:
        messages = messages[:2]

    for m in messages:
        cleaned.append({"name": m.name, "role": m.role, "content": m.content})

    # If no explicit end produced and not initial, let monitor decide
    has_explicit_end = bool(out.scenarioresultat and out.tilbakemelding)
    if (not is_initial) and (not has_explicit_end):
        async def _monitor() -> EndDecision:
            ctx = {
                "difficulty": str(st.session_state.get("difficulty", "")),
                "user_name": str(st.session_state.get("user_name", "")),
                "turn_count": str(st.session_state.get("turns", 0)),
                "max_turns": str(st.session_state.get("max_turns", 6)),
            }
            summary = {
                "meldinger": [m.dict() for m in out.meldinger] if out.meldinger else [],
                "scenarioresultat": (out.scenarioresultat.dict() if out.scenarioresultat else None),
                "tilbakemelding": (out.tilbakemelding.dict() if out.tilbakemelding else None),
            }
            monitor_input = json.dumps(summary, ensure_ascii=False)
            res = await Runner.run(end_monitor_agent, monitor_input, context=ctx)
            out_val = res.final_output
            if isinstance(out_val, EndDecision):
                return out_val
            if isinstance(out_val, dict):
                try:
                    return EndDecision(**out_val)
                except Exception:
                    return EndDecision(should_end=False)
            if isinstance(out_val, str):
                try:
                    data = json.loads(out_val)
                    if isinstance(data, dict):
                        return EndDecision(**data)
                except Exception:
                    pass
            return EndDecision(should_end=False)

        decision: EndDecision = run_async(_monitor())
        if decision and decision.should_end:
            st.session_state.last_meta = {
                "oppdrag": (out.oppdrag.beskrivelse if out.oppdrag else None),
                "sjekkliste": out.sjekkliste or [],
                "scenarioresultat": {"name": "Scenarioresultat", "role": "system", "content": decision.result or ""},
                "tilbakemelding": {"name": "Tilbakemelding", "role": "system", "content": decision.feedback or ""},
            }

    return cleaned
